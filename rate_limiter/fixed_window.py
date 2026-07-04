# rate_limiter/fixed_window.py
import time
from redis import Redis

class FixedWindowLimiter:
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        
        self.LUA_SCRIPT = """
        local current_count = redis.call('INCR', KEYS[1])
        if current_count == 1 then
            redis.call('EXPIRE', KEYS[1], ARGV[1])
        end
        return current_count
        """
        self.lua_executor = self.redis.register_script(self.LUA_SCRIPT)

    def is_allowed(self, client_id: str, limit: int, window_seconds: int) -> bool:
        current_time = int(time.time())
        window_bucket = current_time // window_seconds
        redis_key = f"rl:fixed:{client_id}:{window_bucket}"
        
        try:
            current_count = self.lua_executor(keys=[redis_key], args=[window_seconds])
            print(f"--- Key: {redis_key} | Redis Count: {current_count} | Limit: {limit} ---", flush=True)
            if int(current_count) > limit:
                return False
            return True
        except Exception as e:
            print(f" RATE LIMITER ERROR: {e}", flush=True)
            return True