# app/main.py
from fastapi import FastAPI, Request, HTTPException
from redis import Redis
from rate_limiter.fixed_window import FixedWindowLimiter
from rate_limiter.sliding_window import SlidingWindowLogLimiter
from rate_limiter.token_bucket import TokenBucketLimiter
app = FastAPI()

redis_client = Redis(host='redis', port=6379, db=0, decode_responses=True)
limiter = TokenBucketLimiter(redis_client)

@app.get("/api/data")
def get_data(request: Request):
    client_ip = request.client.host
    
    capacity = 5
    refill_rate= 0.2
    # Back to clean, standard middleware exception patterns
    if not limiter.is_allowed(client_ip, capacity,refill_rate ):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Try again in a few seconds."
        )
        
    return {"message": "Success! Here is your data."}