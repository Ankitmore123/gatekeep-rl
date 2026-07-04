import time
from redis import Redis

class SlidingWindowLogLimiter:
    def _init_(self,redis_client:Redis):
        self.redis = redis_client
        self.LUA_SCRIPT = """
        local key  = KEYS[1] 
        local now = tonumber(ARGV[1])
        local window = tonumber(ARGV[2])
        local limit = tonumber(ARGV[3])
        local clear_before = now - window
        redis.call('ZREMRANGEBYSCORE',key, '-inf' ,clear_before)
        local current_requests =redis.call('ZCARD',key)
        
        if current_requests <limit then
            redis.call('ZADD',key,now,now)
            redis.call('EXPIRE',key,window)
            return 1
        else
            return 0
        end
        
        """
        self.lua_executor = self.redis.register_script(self.LUA_SCRIPT)
def is_allowed(self, client_id: str, limit: int, window_seconds: int) -> bool:
        redis_key = f"rl:sliding:{client_id}"
        current_time = time.time()
        
        try:
            result = self.lua_executor(
                keys=[redis_key],
                args=[current_time, window_seconds, limit]
            )
            return bool(result)
        except Exception as e:
            print(f"SLIDING WINDOW ERROR: {e}", flush=True)
            return True  # Fail-open