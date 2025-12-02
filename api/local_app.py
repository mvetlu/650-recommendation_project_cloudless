from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from psycopg2.extras import RealDictCursor
import time
import random
import json
import os

app = FastAPI(
    title="Recommendation API - Local",
    version="1.0.0",
    description="Local server baseline for comparison against cloud (EC2 + DynamoDB + S3 + CloudWatch)"
)

# OPTIONAL: enable if you need CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Database Configuration ---
DB_CONFIG = {
    "host": "localhost",
    "database": "recommendations",
    "user": "s4p",
    "password": os.getenv("DB_PASSWORD", "")
}


def get_db():
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)


# --- Recommendation Engine Mock Data (same as cloud for fairness) ---
ITEM_CATALOG = [f"item_{i}" for i in range(1, 101)]

PRECOMPUTED_RECS = {
    "1": [{"item_id": f"item_{i}", "score": round(random.uniform(0.5, 1.0), 3)}
          for i in range(1, 21)]
}



def log_local_request(user_id: str, latency_ms: float, limit: int, success: bool, error_msg: str = ""):
    """Write request log to local_requests table."""
    try:
        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO local_requests (user_id, timestamp, latency_ms, limit_val, success, error_message)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            user_id,
            int(time.time()),
            round(latency_ms, 2),
            limit,
            success,
            error_msg
        ))

        conn.commit()
        cur.close()
        conn.close()

    except Exception as e:
        print("Failed to write local log:", e)



@app.get("/health")
async def health():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        cur.close()
        conn.close()

        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": time.time(),
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": time.time(),
        }



@app.get("/recommend/{user_id}")
async def recommend(user_id: str, limit: int = 10, request: Request = None):

    if limit < 1 or limit > 20:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 20")

    start = time.time()
    success = True
    error_msg = ""
    latency_ms = 0.0

    try:
        # Same logic as cloud for fairness
        if user_id not in PRECOMPUTED_RECS:
            recs = [
                {
                    "item_id": random.choice(ITEM_CATALOG),
                    "score": round(random.uniform(0.1, 1.0), 3)
                }
                for _ in range(limit)
            ]
        else:
            recs = PRECOMPUTED_RECS[user_id][:limit]

        latency_ms = (time.time() - start) * 1000

        # Log success request locally
        log_local_request(user_id, latency_ms, limit, success=True)

        return {
            "user_id": user_id,
            "recommendations": recs,
            "latency_ms": round(latency_ms, 2),
            "local_storage": "PostgreSQL local_requests table",
        }

    except Exception as e:
        success = False
        error_msg = str(e)

        # Log failure request locally too
        log_local_request(user_id, 0.0, limit, success=False, error_msg=error_msg)

        raise HTTPException(status_code=500, detail="Internal server error")



@app.get("/crash")
async def crash():
    raise RuntimeError("Manual crash triggered")



if __name__ == "__main__":
    import uvicorn
    print("Starting Local API (PostgreSQL logging enabled)")
    uvicorn.run(app, host="0.0.0.0", port=8000)
