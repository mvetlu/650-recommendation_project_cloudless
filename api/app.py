from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import time
from typing import List, Dict, Any
import uvicorn
import random

app = FastAPI(
    title="Recommendation API - No Cloud",
    description="Single-server recommendation engine on a single node (no external DB)",
    version="1.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------------------------------------------
# In-memory "fake database" so we don't depend on PostgreSQL at all.
# This is enough for your project to demonstrate recommendations + latency.
# --------------------------------------------------------------------------------------

# Pretend we have 100 items in the catalog
ITEM_CATALOG = [f"item_{i}" for i in range(1, 101)]

# Pretend we have some precomputed recs per user
PRECOMPUTED_RECS = {
    "1": [{"item_id": f"item_{i}", "score": round(random.uniform(0.5, 1.0), 3)}
          for i in range(1, 21)],
    "2": [{"item_id": f"item_{i}", "score": round(random.uniform(0.3, 0.9), 3)}
          for i in range(21, 41)],
    "3": [{"item_id": f"item_{i}", "score": round(random.uniform(0.2, 0.85), 3)}
          for i in range(41, 61)],
}


@app.get("/")
async def root():
    return {
        "service": "Recommendation Engine",
        "version": "1.1.0",
        "architecture": "no-cloud",
        "deployment": "single EC2 instance",
        "limitations": [
            "No auto-scaling",
            "Single point of failure",
            "No geographic distribution",
            "No external database (in-memory only)"
        ]
    }


@app.get("/health")
async def health_check():
    # Always "healthy" for this demo (no DB dependency)
    return {
        "status": "healthy",
        "database": "not_used",
        "timestamp": time.time()
    }


@app.get("/recommend/{user_id}")
async def get_recommendations(user_id: str, limit: int = 10):
    """
    No-DB recommendation endpoint.
    - Uses in-memory fake/precomputed recommendations.
    - Always returns quickly (good for latency metrics).
    """
    start_time = time.time()

    if limit < 1 or limit > 20:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 20")

    # If we don't have this user, just randomly recommend some items
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
        "architecture": "no-cloud (in-memory)"
    }


@app.get("/stats")
async def get_stats():
    """
    Just returns static/fake stats so the endpoint still works.
    """
    return {
        "users": len(PRECOMPUTED_RECS),
        "items": len(ITEM_CATALOG),
        "interactions": 0,
        "users_with_recommendations": len(PRECOMPUTED_RECS),
        "architecture": "no-cloud (in-memory)",
        "database": "none",
        "caching": "N/A",
        "auto_scaling": "disabled"
    }


@app.post("/interaction")
async def record_interaction(user_id: str, item_id: str, rating: float):
    """
    For the demo, we just accept the interaction and pretend to store it.
    No DB writes are actually performed.
    """
    if rating < 1.0 or rating > 5.0:
        raise HTTPException(status_code=400, detail="Rating must be between 1.0 and 5.0")

    # In a real system we'd insert into a DB or send to Kafka/Kinesis.
    # Here we just acknowledge it.
    return {
        "status": "success",
        "message": "Interaction received (not persisted in this demo)",
        "note": "No-DB architecture for class project"
    }


if __name__ == "__main__":
    print("Starting No-Cloud Recommendation API (no PostgreSQL)")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        workers=1,
        log_level="info"
    )
