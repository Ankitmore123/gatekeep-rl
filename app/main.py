# app/main.py
from fastapi import FastAPI, Request, HTTPException
from redis import Redis
from rate_limiter.fixed_window import FixedWindowLimiter
from rate_limiter.sliding_window import SlidingWindowLogLimiter

app = FastAPI()

redis_client = Redis(host='redis', port=6379, db=0, decode_responses=True)
limiter = SlidingWindowLogLimiter(redis_client)

@app.get("/api/data")
def get_data(request: Request):
    client_ip = request.client.host
    
    MAX_REQUESTS = 5
    WINDOW_SECONDS = 60
    
    if not limiter.is_allowed(client_ip, MAX_REQUESTS, WINDOW_SECONDS):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Try again in a few seconds."
        )
        
    return {"message": "Success! Here is your data."}