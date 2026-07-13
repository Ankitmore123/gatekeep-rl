import time

class NaiveCounterLimiter:
    def __init__(self, redis_client):
        self.redis = redis_client

    def is_allowed(self, client_id: str, capacity: int) -> bool:
        key = f"rl:naive:{client_id}"
        current = int(self.redis.get(key) or 0)
        if current < capacity:
            time.sleep(0.05)
            self.redis.incr(key)
            return True
        return False