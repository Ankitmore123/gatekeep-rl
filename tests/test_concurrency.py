import threading
from concurrent.futures import ThreadPoolExecutor

import pytest
from redis import Redis

from rate_limiter.naive_limiter import NaiveCounterLimiter
from rate_limiter.fixed_window import FixedWindowLimiter
from rate_limiter.token_bucket import TokenBucketLimiter
from rate_limiter.sliding_window import SlidingWindowLogLimiter

CAPACITY = 5
CONCURRENCY = 30


@pytest.fixture
def redis_client():
    r = Redis(host="127.0.0.1", port=6379, db=0, decode_responses=True)
    r.flushall()
    yield r
    r.flushall()


def hammer(is_allowed_fn, num_threads: int):
    barrier = threading.Barrier(num_threads)
    results = [None] * num_threads

    def worker(i):
        barrier.wait()
        results[i] = is_allowed_fn()

    with ThreadPoolExecutor(max_workers=num_threads) as pool:
        futures = [pool.submit(worker, i) for i in range(num_threads)]
        for f in futures:
            f.result()
    return results


def test_naive_limiter_overadmits_under_concurrency(redis_client):
    limiter = NaiveCounterLimiter(redis_client)
    results = hammer(lambda: limiter.is_allowed("racer", CAPACITY), CONCURRENCY)
    allowed = sum(results)
    print(f"\n[naive] allowed={allowed}")
    assert allowed > CAPACITY


def test_fixed_window_holds_limit_under_concurrency(redis_client):
    limiter = FixedWindowLimiter(redis_client)
    results = hammer(lambda: limiter.is_allowed("racer", CAPACITY, 60), CONCURRENCY)
    print(f"\n[fixed_window] allowed={sum(results)}")
    assert sum(results) == CAPACITY


def test_token_bucket_holds_limit_under_concurrency(redis_client):
    limiter = TokenBucketLimiter(redis_client)
    results = hammer(lambda: limiter.is_allowed("racer", CAPACITY, 0.2), CONCURRENCY)
    print(f"\n[token_bucket] allowed={sum(results)}")
    assert sum(results) == CAPACITY


def test_sliding_window_holds_limit_under_concurrency(redis_client):
    limiter = SlidingWindowLogLimiter(redis_client)
    results = hammer(lambda: limiter.is_allowed("racer", CAPACITY, 60), CONCURRENCY)
    print(f"\n[sliding_window] allowed={sum(results)}")
    assert sum(results) == CAPACITY