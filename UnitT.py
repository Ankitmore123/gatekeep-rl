import pytest
from redis import Redis
import threading
from concurrent.futures import ThreadPoolExecutor
import time 

# Import your actual rate limiter implementations here
from rate_limiter.token_bucket import TokenBucketLimiter
from rate_limiter.sliding_window import SlidingWindowLogLimiter

@pytest.fixture
def redis_client():
    r = Redis(host="127.0.0.1", port=6379, db=0, decode_responses=True)
    r.flushall()
    yield r
    r.flushall()

def hammer(is_allowed_fn, num_threads):
    barrier = threading.Barrier(num_threads)
    results = [None] * num_threads
    
    def worker(i):
        barrier.wait()  # Synchronize all threads to fire at the exact same instant
        results[i] = is_allowed_fn()
        
    with ThreadPoolExecutor(max_workers=num_threads) as pool:
        futures = [pool.submit(worker, i) for i in range(num_threads)]
        for f in futures:
            f.result()
    return results


class NaiveCounterLimiter:
    def __init__(self, redis_client):
        self.redis = redis_client
        
    def is_allowed(self, client_id: str, capacity: int) -> bool:
        key = f"rl:naive:{client_id}"
        current = int(self.redis.get(key) or 0)
        if current < capacity:
            time.sleep(0.05)  # Force context switch to guarantee race condition
            self.redis.incr(key)
            return True
        return False

CAPACITY = 5
CONCURRENCY = 30

def test_naive_limiter_overadmits_under_concurrency(redis_client):
    limiter = NaiveCounterLimiter(redis_client)
    results = hammer(lambda: limiter.is_allowed("racer", CAPACITY), CONCURRENCY)
    allowed = sum(results)   
    
    print(f"\n[Naive] Allowed {allowed} requests out of {CAPACITY} quota!")
    assert allowed > CAPACITY  # Proves it breaches the limit

def test_sliding_window_maintains_atomicity(redis_client):
    limiter = SlidingWindowLogLimiter(redis_client)
    WINDOW_SECONDS = 60
    
    results = hammer(
        lambda: limiter.is_allowed("racer", CAPACITY, WINDOW_SECONDS), 
        CONCURRENCY
    )
    allowed = sum(results)
    
    print(f"\n[Sliding Window] Allowed {allowed} requests out of {CAPACITY} quota!")
    assert allowed == CAPACITY  # MUST be exactly equal to capacity

# 
def test_token_bucket_maintains_atomicity(redis_client):
    limiter = TokenBucketLimiter(redis_client)
    REFILL_RATE = 0.2
    
    results = hammer(
        lambda: limiter.is_allowed("racer", CAPACITY, REFILL_RATE), 
        CONCURRENCY
    )
    allowed = sum(results)
    
    print(f"\n[Token Bucket] Allowed {allowed} requests out of {CAPACITY} quota!")
    assert allowed == CAPACITY  # MUST be exactly equal to capacity