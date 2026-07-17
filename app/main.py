# app/main.py
from fastapi import FastAPI, Request, HTTPException, Header
from redis import Redis
from rate_limiter.fixed_window import FixedWindowLimiter
from rate_limiter.sliding_window import SlidingWindowLogLimiter
from rate_limiter.token_bucket import TokenBucketLimiter
app = FastAPI()

redis_client = Redis(host='redis', port=6379, db=0, decode_responses=True)
limiter = TokenBucketLimiter(redis_client)
TIER_CONFIGS = { #value is a dictionary 
    "free":{
        "capacity" : 5,
        "refill_rate" : 0.2 
    },
    "pro": {
        "capacity": 20,
        "refill_rate": 1.0        
    },
    "enterprise": {
        "capacity": 100,
        "refill_rate": 10.0       
    }
    
}
@app.get("/api/data")
def get_data(x_api_key :str = Header(None)):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API Key missing in headers.")
    
    if "enterprise" in x_api_key.lower():
        tier_name = "enterprise"
    elif "pro" in x_api_key.lower():
        tier_name = "pro"
    else:
        tier_name = "free"
    capacity = 5
    refill_rate= 0.2
    CONFIG = TIER_CONFIGS[tier_name]
    redis_key = f"{tier_name}:{x_api_key}"
    # Back to clean, standard middleware exception patterns
    if not limiter.is_allowed(redis_key, CONFIG["capacity"] ,CONFIG["refill_rate"]):
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded for your '{tier_name}' tier profile"
        )
        
    return {"message": "Success! Here is your data."}
@app.get("/api/sliding-data")
def get_sliding_data(request: Request):
    user_id = request.headers.get("X-User-ID", request.client.host)
    if not limiter.is_allowed(user_id, 5, 60):
        raise HTTPException(status_code=429, detail="Rate limit exceeded.")
    return {"message": "sliding window ok"}

@app.get("/api/token-bucket-data")
def get_token_bucket_data(request: Request):
    user_id = request.headers.get("X-User-ID", request.client.host)
    if not limiter.is_allowed(user_id, 5, 0.2):
        raise HTTPException(status_code=429, detail="Rate limit exceeded.")
    return {"message": "token bucket ok"}