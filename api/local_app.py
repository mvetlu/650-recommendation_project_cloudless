@app.get("/recommend/{user_id}")
async def recommend(user_id: str, limit: int = 10, request: Request = None):

    if limit < 1 or limit > 20:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 20")

    # START TIMER HERE (correct)
    start = time.perf_counter()
    success = True
    error_msg = ""

    try:
        # ---- Recommendation Logic ----
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

        # ---- END TIMER HERE ----
        latency_ms = (time.perf_counter() - start) * 1000

        # Log into PostgreSQL
        log_local_request(user_id, latency_ms, limit, success=True)

        return {
            "user_id": user_id,
            "recommendations": recs,
            "latency_ms": round(latency_ms, 2),
            "local_storage": "PostgreSQL local_requests table",
        }

    except Exception as e:
        latency_ms = 0
        success = False
        error_msg = str(e)

        log_local_request(user_id, 0.0, limit, success=False, error_message=error_msg)
        raise HTTPException(status_code=500, detail="Internal server error")
