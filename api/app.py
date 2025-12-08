from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import psycopg2
from psycopg2.extras import RealDictCursor
import time
import os
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
    "host": "localhost",
    "database": "recommendations",
    "user": "s4p",
    "password": os.getenv("DB_PASSWORD", ""),
}


def get_db_connection():
    try:
        return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Database connection failed: {str(e)}"
        )


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
            "No DDoS protection",
        ],
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
async def get_recommendations(user_id: str, limit: int = 10):
    start_time = time.time()

    if limit < 1 or limit > 20:
        raise HTTPException(
            status_code=400,
            detail="Limit must be between 1 and 20",
        )

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT recommended_items, computed_at "
            "FROM recommendations WHERE user_id = %s",
            (user_id,),
        )
        result = cursor.fetchone()

        if not result:
            cursor.close()
            conn.close()
            raise HTTPException(
                status_code=404,
                detail=f"No recommendations found for user: {user_id}",
            )

        recommendations = result["recommended_items"][:limit]
        computed_at = result["computed_at"]

        item_ids = [rec["item_id"] for rec in recommendations]
        cursor.execute(
            "SELECT item_id FROM items WHERE item_id = ANY(%s)",
            (item_ids,),
        )
        items = {row["item_id"]: dict(row) for row in cursor.fetchall()}

        enriched_recommendations = []
        for rec in recommendations:
            item_id = rec["item_id"]
            if item_id in items:
                enriched_recommendations.append(
                    {
                        "item_id": item_id,
                        "predicted_score": rec["score"],
                    }
                )

        cursor.close()
        conn.close()

        latency_ms = (time.time() - start_time) * 1000

        return {
            "user_id": user_id,
            "recommendations": enriched_recommendations,
            "count": len(enriched_recommendations),
            "computed_at": computed_at.isoformat() if computed_at else None,
            "latency_ms": round(latency_ms, 2),
            "architecture": "no-cloud",
        }

    except HTTPException:
        raise
    except Exception as e:
        if conn:
            conn.close()
        raise HTTPException(
            status_code=500,
            detail=f"Internal error: {str(e)}",
        )


@app.get("/stats")
async def get_stats():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) AS count FROM users")
        num_users = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) AS count FROM items")
        num_items = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) AS count FROM interactions")
        num_interactions = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) AS count FROM recommendations")
        num_recommendations = cursor.fetchone()["count"]

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
            "auto_scaling": "disabled",
        }

    except Exception as e:
        if conn:
            conn.close()
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching stats: {str(e)}",
        )


@app.get("/stats/ui", response_class=HTMLResponse)
async def stats_ui():
    """
    Human-friendly dashboard view over the same stats as /stats.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) AS count FROM users")
        num_users = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) AS count FROM items")
        num_items = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) AS count FROM interactions")
        num_interactions = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) AS count FROM recommendations")
        num_recommendations = cursor.fetchone()["count"]

        cursor.close()
        conn.close()

        # NOTE: double braces {{ }} are required inside an f-string for CSS
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>No-Cloud Recommendation Stats</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            background: #0b0c10;
            color: #e5e5e5;
            margin: 0;
            padding: 2rem;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
        }}
        h1 {{
            margin-bottom: 0.25rem;
        }}
        .subtitle {{
            color: #9ca3af;
            margin-bottom: 1.5rem;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }}
        .card {{
            background: #111827;
            border-radius: 0.75rem;
            border: 1px solid #1f2937;
            padding: 1rem 1.25rem;
        }}
        .label {{
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #9ca3af;
            margin-bottom: 0.25rem;
        }}
        .value {{
            font-size: 1.5rem;
            font-weight: 600;
        }}
        .meta {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.75rem;
            font-size: 0.85rem;
            color: #9ca3af;
        }}
        .pill {{
            border-radius: 999px;
            border: 1px solid #374151;
            padding: 0.25rem 0.75rem;
            background: #020617;
        }}
        a {{
            color: #38bdf8;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
<div class="container">
    <h1>No-Cloud Recommendation Service</h1>
    <div class="subtitle">
        Local FastAPI + PostgreSQL instance — live stats from the current database.
    </div>

    <div class="grid">
        <div class="card">
            <div class="label">Users</div>
            <div class="value">{num_users}</div>
        </div>
        <div class="card">
            <div class="label">Items</div>
            <div class="value">{num_items}</div>
        </div>
        <div class="card">
            <div class="label">Interactions</div>
            <div class="value">{num_interactions}</div>
        </div>
        <div class="card">
            <div class="label">Users with Recommendations</div>
            <div class="value">{num_recommendations}</div>
        </div>
    </div>

    <div class="card">
        <div class="label">Architecture</div>
        <div class="meta">
            <span class="pill">Mode: no-cloud (single host)</span>
            <span class="pill">DB: PostgreSQL (single instance)</span>
            <span class="pill">Caching: none</span>
            <span class="pill">Auto-scaling: disabled</span>
        </div>
        <p style="margin-top: 1rem; font-size: 0.9rem; color: #9ca3af;">
            This view is just a human-friendly wrapper around the
            <code>/stats</code> JSON endpoint.
            For programmatic access, use
            <a href="/stats">/stats</a>;
            for API docs, visit
            <a href="/docs">/docs</a>.
        </p>
    </div>
</div>
</body>
</html>
"""
        return HTMLResponse(content=html)

    except Exception as e:
        if conn:
            conn.close()
        raise HTTPException(
            status_code=500,
            detail=f"Error rendering stats UI: {str(e)}",
        )


@app.post("/interaction")
async def record_interaction(user_id: str, item_id: str, rating: float):
    if rating < 1.0 or rating > 5.0:
        raise HTTPException(
            status_code=400,
            detail="Rating must be between 1.0 and 5.0",
        )

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO interactions (user_id, item_id, rating, timestamp)
            VALUES (%s, %s, %s, %s)
            """,
            (user_id, item_id, rating, int(time.time())),
        )

        conn.commit()
        cursor.close()
        conn.close()

        return {
            "status": "success",
            "message": "Interaction recorded",
            "note": "Recommendations will be updated in next batch re-computation",
        }

    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        raise HTTPException(
            status_code=500,
            detail=f"Error recording interaction: {str(e)}",
        )


if __name__ == "__main__":
    print("Starting No-Cloud Recommendation API")
    print("Architecture: Single-threaded server on localhost")
    print("Database: PostgreSQL (no connection pooling)")
    print("Scaling: None (fixed capacity)")
    print("Monitoring: Basic logging only")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        workers=1,
        log_level="info",
    )