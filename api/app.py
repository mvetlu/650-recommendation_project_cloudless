from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import random
import logging
import os
from collections import defaultdict


# Create logs directory
os.makedirs("logs", exist_ok=True)

# Local log file (failures.log)
logging.basicConfig(
    filename="logs/failures.log",
    level=logging.WARNING,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Logger object
logger = logging.getLogger("failure_logger")

# ALSO log warnings/errors to stdout so CloudWatch can ingest them
stdout_handler = logging.StreamHandler()
stdout_handler.setLevel(logging.WARNING)
stdout_handler.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))
logger.addHandler(stdout_handler)



app = FastAPI(
    title="Recommendation API",
    description="Cloud + Local logging, Failure logging, Rate limiting demo",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



RATE_LIMIT_MAX = 150
RATE_LIMIT_WINDOW = 180  # seconds

request_counts = defaultdict(list)



@app.middleware("http")
async def rate_limiter(request: Request, call_next):
    ip = request.client.host
    now = time.time()

    window = [t for t in request_counts[ip] if now - t < RATE_LIMIT_WINDOW]
    request_counts[ip] = window
    request_counts[ip].append(now)

    if len(window) > RATE_LIMIT_MAX:
        logger.warning(
            f"RATE LIMIT TRIGGERED: {ip} exceeded {RATE_LIMIT_MAX} requests"
        )
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests (Rate limit activated)"}
        )

    response = await call_next(request)
    return response


@app.middleware("http")
async def failure_logging(request: Request, call_next):
    try:
        response = await call_next(request)

        if response.status_code >= 400:
            logger.warning(
                f"FAILURE: {request.method} {request.url} → Status {response.status_code}"
            )

        return response

    except Exception as e:
        logger.error(
            f"EXCEPTION: {request.method} {request.url} → Error: {str(e)}"
        )
        raise e



ITEM_CATALOG = [f"item_{i}" for i in range(1, 101)]

PRECOMPUTED_RECS = {
    "1": [{"item_id": f"item_{i}", "score": round(random.uniform(0.5, 1.0), 3)}
          for i in range(1, 21)]
}



@app.get("/")
async def root():
    return {
        "service": "Recommendation Engine",
        "version": "2.0.0",
        "logging": "CloudWatch + Local Failures.log",
        "rate_limiting": True
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "logging": "enabled",
        "cloudwatch_ready": True
    }


@app.get("/recommend/{user_id}")
async def recommend(user_id: str, limit: int = 10):

    if limit < 1 or limit > 20:
        logger.warning(f"Invalid 'limit' value: {limit}")
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 20")

    start = time.time()

    if user_id not in PRECOMPUTED_RECS:
        recs = [
            {"item_id": random.choice(ITEM_CATALOG),
             "score": round(random.uniform(0.1, 1.0), 3)}
            for _ in range(limit)
        ]
    else:
        recs = PRECOMPUTED_RECS[user_id][:limit]

    latency = (time.time() - start) * 1000

    return {
        "user_id": user_id,
        "recommendations": recs,
        "latency_ms": round(latency, 2)
    }


@app.get("/crash")
async def crash():
    logger.error("Manual crash triggered for failure test")
    raise RuntimeError("Simulated crash")



if __name__ == "__main__":
    import uvicorn
    print("Starting API with logging + CloudWatch support")
    uvicorn.run(app, host="0.0.0.0", port=8000)
