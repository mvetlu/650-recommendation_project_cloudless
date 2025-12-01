from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import random
import uvicorn
import os

app = FastAPI(
    title="Recommendation API",
    description="Single-server recommendation engine on EC2 with security + failure tests",
    version="1.2.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


RATE_LIMIT_WINDOW = 180   
RATE_LIMIT_MAX = 150      
ip_hits = {}              

@app.middleware("http")
async def rate_limiter(request: Request, call_next):
    client_ip = request.client.host
    now = time.time()

    # Clean old request timestamps
    if client_ip in ip_hits:
        ip_hits[client_ip] = [t for t in ip_hits[client_ip] if now - t < RATE_LIMIT_WINDOW]
    else:
        ip_hits[client_ip] = []

    # Check limit
    if len(ip_hits[client_ip]) >= RATE_LIMIT_MAX:
        return JSONResponse(
            {"error": "Rate limit exceeded. Too many requests. Try again later."},
            status_code=429
        )

    # Record request timestamp
    ip_hits[client_ip].append(now)

    response = await call_next(request)
    return response


ITEM_CATALOG = [f"item_{i}" for i in range(1, 101)]

PRECOMPUTED_RECS = {
    "1": [{"item_id": f"item_{i}", "score": round(random.uniform(0.5, 1.0), 3)}
          for i in range(1, 21)],
    "2": [{"item_id": f"item_{i}", "score": round(random.uniform(0.3, 0.9), 3)}
          for i in range(21, 41)],
    "3": [{"item_id": f"item_{i}", "score": round(random.uniform(0.2, 0.85), 3)}
          for i in range(41, 61)],
}

DB_OK = True  # Toggle in demo to simulate DB failure




@app.get("/")
async def root():
    return {
        "service": "Recommendation Engine",
        "version": "1.2.0",
        "architecture": "cloud (EC2)",
        "features": [
            "Rate limiting",
            "Crash simulation",
            "Health endpoint with DB failure simulation",
            "Stress test / failure recovery",
            "In-memory recommendations"
        ]
    }


@app.get("/health")
async def health_check():
    if not DB_OK:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "timestamp": time.time()
        }

    return {
        "status": "healthy",
        "database": "connected",
        "timestamp": time.time()
    }


@app.get("/recommend/{user_id}")
async def get_recommendations(user_id: str, limit: int = 10):
    start_time = time.time()

    if limit < 1 or limit > 20:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 20")

    if user_id not in PRECOMPUTED_RECS:
        recs = [
            {"item_id": random.choice(ITEM_CATALOG), "score": round(random.uniform(0.1, 1.0), 3)}
            for _ in range(limit)
        ]
        computed_at = None
    else:
        full_list = PRECOMPUTED_RECS[user_id]
        recs = full_list[:limit]
        computed_at = time.time()

    latency_ms = (time.time() - start_time) * 1000

    return {
        "user_id": user_id,
        "recommendations": recs,
        "count": len(recs),
        "computed_at": computed_at,
        "latency_ms": round(latency_ms, 2),
        "architecture": "cloud (in-memory)"
    }


@app.get("/stats")
async def get_stats():
    return {
        "users": len(PRECOMPUTED_RECS),
        "items": len(ITEM_CATALOG),
        "interactions": 0,
        "architecture": "cloud (in-memory)",
        "database": "none",
        "auto_scaling": "disabled"
    }


@app.post("/interaction")
async def record_interaction(user_id: str, item_id: str, rating: float):

    if rating < 1.0 or rating > 5.0:
        raise HTTPException(status_code=400, detail="Rating must be between 1.0 and 5.0")

    return {
        "status": "success",
        "message": "Interaction received (not persisted)",
        "note": "This is a stateless EC2 demo"
    }



@app.get("/crash")
async def crash_server():
    os._exit(1)   



if __name__ == "__main__":
    print("Starting Cloud Recommendation API with security & failure tests")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        workers=1,
        log_level="info"
    )
