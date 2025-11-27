from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import time
import os
from typing import List, Dict, Any
import uvicorn

app = FastAPI(
    title="Recommendation API - No Cloud",
    description="Single-server recommendation engine on localhost",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_CONFIG = {
    'host': 'localhost',
    'database': 'recommendations',
    'user': "s4p",
    'password': os.getenv('DB_PASSWORD', '')
}


def get_db_connection():
    try:
        return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database connection failed: {str(e)}")


@app.get("/")
async def root():
    return {
        "service": "Recommendation Engine",
        "version": "1.0.0",
        "architecture": "no-cloud",
        "deployment": "single MacBook Pro server",
        "limitations": [
            "No auto-scaling",
            "Single point of failure",
            "No geographic distribution",
            "No DDoS protection"
        ]
    }


@app.get("/health")
async def health_check():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()

        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": time.time()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": time.time()
        }


@app.get("/recommend/{user_id}")
async def get_recommendations(user_id: str, limit: int = 10):
    start_time = time.time()

    if limit < 1 or limit > 20:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 20")

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT recommended_items, computed_at FROM recommendations WHERE user_id = %s",
            (user_id,)
        )
        result = cursor.fetchone()

        if not result:
            cursor.close()
            conn.close()
            raise HTTPException(
                status_code=404,
                detail=f"No recommendations found for user: {user_id}"
            )

        recommendations = result['recommended_items'][:limit]
        computed_at = result['computed_at']

        item_ids = [rec['item_id'] for rec in recommendations]
        cursor.execute(
            "SELECT item_id FROM items WHERE item_id = ANY(%s)",
            (item_ids,)
        )
        items = {row['item_id']: dict(row) for row in cursor.fetchall()}

        enriched_recommendations = []
        for rec in recommendations:
            item_id = rec['item_id']
            if item_id in items:
                enriched_recommendations.append({
                    "item_id": item_id,
                    "predicted_score": rec['score']
                })

        cursor.close()
        conn.close()

        latency_ms = (time.time() - start_time) * 1000

        return {
            "user_id": user_id,
            "recommendations": enriched_recommendations,
            "count": len(enriched_recommendations),
            "computed_at": computed_at.isoformat() if computed_at else None,
            "latency_ms": round(latency_ms, 2),
            "architecture": "no-cloud"
        }

    except HTTPException:
        raise
    except Exception as e:
        if conn:
            conn.close()
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.get("/stats")
async def get_stats():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Count users
        cursor.execute("SELECT COUNT(*) as count FROM users")
        num_users = cursor.fetchone()['count']

        # Count items
        cursor.execute("SELECT COUNT(*) as count FROM items")
        num_items = cursor.fetchone()['count']

        # Count interactions
        cursor.execute("SELECT COUNT(*) as count FROM interactions")
        num_interactions = cursor.fetchone()['count']

        # Count precomputed recommendations
        cursor.execute("SELECT COUNT(*) as count FROM recommendations")
        num_recommendations = cursor.fetchone()['count']

        cursor.close()
        conn.close()

        return {
            "users": num_users,
            "items": num_items,
            "interactions": num_interactions,
            "users_with_recommendations": num_recommendations,
            "architecture": "no-cloud",
            "database": "PostgreSQL (single instance)",
            "caching": "none",
            "auto_scaling": "disabled"
        }

    except Exception as e:
        if conn:
            conn.close()
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")


@app.post("/interaction")
async def record_interaction(user_id: str, item_id: str, rating: float):
    if rating < 1.0 or rating > 5.0:
        raise HTTPException(status_code=400, detail="Rating must be between 1.0 and 5.0")

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Insert interaction
        cursor.execute(
            """
            INSERT INTO interactions (user_id, item_id, rating, timestamp)
            VALUES (%s, %s, %s, %s)
            """,
            (user_id, item_id, rating, int(time.time()))
        )

        conn.commit()
        cursor.close()
        conn.close()

        return {
            "status": "success",
            "message": "Interaction recorded",
            "note": "Recommendations will be updated in next batch re-computation"
        }

    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        raise HTTPException(status_code=500, detail=f"Error recording interaction: {str(e)}")


if __name__ == "__main__":
    print("Starting No-Cloud Recommendation API")
    print("Architecture: Single-threaded server on localhost")
    print("Database: PostgreSQL (no connection pooling)")
    print("Scaling: None (fixed capacity)")
    print("Monitoring: Basic logging only")

    # Run with single worker (intentional bottleneck)
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        workers=1,  # Single process - bottleneck for demo
        log_level="info"
    )