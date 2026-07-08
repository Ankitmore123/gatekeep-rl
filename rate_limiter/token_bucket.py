import time
from redis import Redis

class TokenBucketLimiter:
    def __init__(self,redis_client:Redis):
        self.redis = redis_client
        self.LUA_SCRIPT= """
        local key = KEYS[1]
        local now = tonumber(ARGV[1])

        local capacity = tonumber(ARGV[2])
        local refill_rate = tonumber(ARGV[3])

        local data = redis.call("HMGET", key, 'tokens', 'last_updated')
        local current_tokens = tonumber(data[1])
        local last_updated = tonumber(data[2])

        if not current_tokens then
            current_tokens = capacity
            last_updated = now
        end

        local time_elapsed = math.max(0, now - last_updated)
        local tokens_to_add = time_elapsed * refill_rate
        local new_tokens = math.min(capacity, current_tokens + tokens_to_add)

        if new_tokens >= 1 then
            new_tokens = new_tokens - 1
            redis.call('HMSET', key, 'tokens', new_tokens, 'last_updated', now)
            redis.call('EXPIRE', key, math.ceil(capacity / refill_rate))
            return 1
        else
            redis.call('HMSET', key, 'tokens', new_tokens, 'last_updated', now)
            return 0
        end
        """
        self.lua_executor = self.redis.register_script(self.LUA_SCRIPT)
    def is_allowed(self,client_id :str , capacity: int ,refill_rate_per_sec :float):
        redis_key = f"rl:token:{client_id}"
        current_time = time.time()
        try:
            result = self.lua_executor(
                keys = [redis_key],
                args = [current_time,capacity, refill_rate_per_sec]
            )
            if result == 1:
                status = "ALLOWED"
            else:
                status = "BLOCKED"
            print(f"--- [Token Bucket] Key: {redis_key} | Status: {status} ---", flush=True)
        except Exception as e:
            print(f"Token BUCKET ERROR :{e}",flush = True)
            return True
            
