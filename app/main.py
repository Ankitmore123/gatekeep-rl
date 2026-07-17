# app/main.py
import os
from fastapi import FastAPI, Request, HTTPException, Header,Query
from redis import Redis
from rate_limiter.fixed_window import FixedWindowLimiter
from rate_limiter.sliding_window import SlidingWindowLogLimiter
from rate_limiter.token_bucket import TokenBucketLimiter
app = FastAPI()

redis_client = Redis(host='redis', port=6379, db=0, decode_responses=True)
limiter = TokenBucketLimiter(redis_client)
TIER_CONFIGS = {
    "free": {"capacity": 30, "refill_rate": 1.0},
    "pro": {"capacity": 150, "refill_rate": 5.0},
    "enterprise": {"capacity": 1000, "refill_rate": 30.0}
}
def verify_and_deduct_quota(x_api_key :str , cost:int):
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
    if not limiter.is_allowed(redis_key, CONFIG["capacity"] ,CONFIG["refill_rate"],cost =cost):
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded for your '{tier_name}' tier profile"
        )
        
    return {"message": "Success! Here is your data."}


@app.get("/api/products/{product_id}")
def get_single_product(product_id: int, x_api_key: str = Header(None)):
    verify_and_deduct_quota(x_api_key, cost=1)
    return {"data": f"Product details for item #{product_id}", "cost_charged": 1}


@app.get("/api/products")
def get_paginated_products(limit: int = Query(default=5, ge=1, le=50), x_api_key: str = Header(None)):
    """CONNECTION: Dynamic cost = 2 base query cost + N rows requested."""
    dynamic_cost = 2 + limit
    verify_and_deduct_quota(x_api_key, cost=dynamic_cost)
    return {
        "data": [f"Product {i}" for i in range(1, limit + 1)], 
        "cost_charged": dynamic_cost
    }


@app.post("/api/products")
def create_product(x_api_key: str = Header(None)):
    """MUTATION: Data modification/write. Cost = 10 Tokens."""
    verify_and_deduct_quota(x_api_key, cost=10)
    return {"message": "Product successfully committed to database.", "cost_charged": 10}