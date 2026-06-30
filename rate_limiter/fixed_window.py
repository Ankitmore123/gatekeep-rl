from fastapi import FastAPI ,Request,HTTPException
import redis 
import time
app = FastAPI()
redis_client = redis.Redis(host= 'redis',port = 6379, db = 0 , decode_responses=True)
LUA_SCRIPT = """
local current_count = redis.call('INCR',KEYS[1]) 
if current_count == 1 then 
    redis.call('EXPIRE' , KEYS[1],ARGV[2])
end
return current_count
"""
rate_limit_script = redis_client.register_script(LUA_SCRIPT)
@app.get("/api/data")
def get_data(request: Request):
    client_ip = request.client.host
    current_window = int(time.time() // 60)
    key = f"rate_limit:{client_ip}:{current_window}"
    MAX_REQUESTS = 5
    WINDOW_SECONDS = 60
    try:
        current_count = rate_limit_script(
            keys = [key]
            args = [MAX_REQUESTS,WINDOW_SECONDS]
            
        )
        if current_count >MAX_REQUESTS:
            raise HTTPException(
                status_code=429,
                detail = "Rate limit exceeded . Try again in few seconds "
            )
    except redis.ConnectionError:
        pass
    return {"message": "Success! Here is your data.", "requests_left": MAX_REQUESTS - current_count}