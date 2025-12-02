from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import random
import logging
import os
from collections import defaultdict
from typing import Any, Dict

import boto3
from botocore.exceptions import BotoCoreError, ClientError
import json
from datetime import datetime, timezone
from decimal import Decimal




AWS_REGION = os.getenv("AWS_REGION", "us-east-2")  

DDB_TABLE_NAME = os.getenv("DDB_TABLE_NAME", "recommendation_requests")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "your-metrics-bucket-name")
CW_NAMESPACE = os.getenv("CW_NAMESPACE", "RecommendationAPI")

# Create AWS clients (they will use the EC2 instance role or ~/.aws/ credentials)
dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
ddb_table = dynamodb.Table(DDB_TABLE_NAME)

s3 = boto3.client("s3", region_name=AWS_REGION)
cloudwatch = boto3.client("cloudwatch", region_name=AWS_REGION)



os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    filename="logs/failures.log",
    level=logging.WARNING,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("failure_logger")

stdout_handler = logging.StreamHandler()
stdout_handler.setLevel(logging.WARNING)
stdout_handler.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))
logger.addHandler(stdout_handler)

app = FastAPI(
    title="Recommendation API (Cloud)",
    description="EC2 + DynamoDB + S3 + CloudWatch demo",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


RATE_LIMIT_MAX = 150          # max requests
RATE_LIMIT_WINDOW = 180       # seconds

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

        # Push a CloudWatch metric for rate limit events
        try:
            cloudwatch.put_metric_data(
                Namespace=CW_NAMESPACE,
                MetricData=[{
                    "MetricName": "RateLimitTriggered",
                    "Value": 1.0,
                    "Unit": "Count"
                }]
            )
        except (BotoCoreError, ClientError) as e:
            logger.warning(f"Failed to send RateLimitTriggered metric: {e}")

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
            # Optional: could also send a CloudWatch metric here

        return response

    except Exception as e:
        logger.error(
            f"EXCEPTION: {request.method} {request.url} → Error: {str(e)}"
        )
        # Send CloudWatch metric for exceptions
        try:
            cloudwatch.put_metric_data(
                Namespace=CW_NAMESPACE,
                MetricData=[{
                    "MetricName": "Exceptions",
                    "Value": 1.0,
                    "Unit": "Count"
                }]
            )
        except (BotoCoreError, ClientError):
            pass

        raise e



ITEM_CATALOG = [f"item_{i}" for i in range(1, 101)]

PRECOMPUTED_RECS = {
    "1": [{"item_id": f"item_{i}", "score": round(random.uniform(0.5, 1.0), 3)}
          for i in range(1, 21)]
}


def log_request_to_dynamodb(user_id: str, latency_ms: float, limit: int, success: bool, error_msg: str = ""):
    """Store a single request record in DynamoDB."""
    try:
        ts = int(time.time())
        ddb_table.put_item(
            Item={
                "request_id": f"{user_id}-{ts}-{random.randint(1000,9999)}",
                "user_id": user_id,
                "timestamp": Decimal(str(ts)),
                "latency_ms": Decimal(str(round(latency_ms, 2))),
                "limit": Decimal(str(limit)),
                "success": Decimal("1") if success else Decimal("0"),
                "error_message": error_msg,
            }
        )
    except (BotoCoreError, ClientError, TypeError) as e:
        logger.warning(f"Failed to write to DynamoDB: {e}")


def upload_metrics_to_s3(payload: Dict[str, Any]):
    """Upload a small JSON metrics blob to S3 per request."""
    try:
        now = datetime.now(timezone.utc).isoformat()
        key = f"metrics/requests/{now}.json"

        s3.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=key,
            Body=json.dumps(payload).encode("utf-8"),
            ContentType="application/json"
        )
    except (BotoCoreError, ClientError) as e:
        logger.warning(f"Failed to upload metrics to S3: {e}")


def send_latency_metric_to_cloudwatch(latency_ms: float):
    """Send custom latency metric to CloudWatch."""
    try:
        cloudwatch.put_metric_data(
            Namespace=CW_NAMESPACE,
            MetricData=[{
                "MetricName": "RequestLatency",
                "Value": latency_ms,
                "Unit": "Milliseconds"
            }]
        )
    except (BotoCoreError, ClientError) as e:
        logger.warning(f"Failed to send latency metric: {e}")



@app.get("/")
async def root():
    return {
        "service": "Recommendation Engine",
        "version": "3.0.0",
        "deployment": "AWS EC2",
        "storage": {
            "requests": "DynamoDB",
            "metrics": "S3",
            "monitoring": "CloudWatch"
        }
    }


@app.get("/health")
async def health():
    """Health check that also verifies AWS connectivity."""
    aws_status = {
        "dynamodb": "unknown",
        "s3": "unknown",
        "cloudwatch": "unknown"
    }

    # Check DynamoDB
    try:
        ddb_table.load()  # simple call to ensure table is reachable
        aws_status["dynamodb"] = "ok"
    except Exception as e:
        aws_status["dynamodb"] = f"error: {e}"

    # Check S3
    try:
        s3.list_buckets()
        aws_status["s3"] = "ok"
    except Exception as e:
        aws_status["s3"] = f"error: {e}"

    # Check CloudWatch
    try:
        cloudwatch.put_metric_data(
            Namespace=CW_NAMESPACE,
            MetricData=[{
                "MetricName": "HealthCheck",
                "Value": 1.0,
                "Unit": "Count"
            }]
        )
        aws_status["cloudwatch"] = "ok"
    except Exception as e:
        aws_status["cloudwatch"] = f"error: {e}"

    return {
        "status": "healthy",
        "timestamp": time.time(),
        "aws": aws_status
    }


@app.get("/recommend/{user_id}")
async def recommend(user_id: str, limit: int = 10, request: Request = None):

    if limit < 1 or limit > 20:
        logger.warning(f"Invalid 'limit' value: {limit}")
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 20")

    start = time.time()
    success = True
    error_msg = ""

    try:
        # Simple recommendation logic (as before)
        if user_id not in PRECOMPUTED_RECS:
            recs = [
                {"item_id": random.choice(ITEM_CATALOG),
                 "score": round(random.uniform(0.1, 1.0), 3)}
                for _ in range(limit)
            ]
        else:
            recs = PRECOMPUTED_RECS[user_id][:limit]

        latency_ms = (time.time() - start) * 1000

        # Build metrics payload
        client_ip = request.client.host if request else "unknown"
        metric_payload = {
            "user_id": user_id,
            "limit": limit,
            "latency_ms": Decimal(str(round(latency_ms, 2))),

            "timestamp": int(time.time()),
            "client_ip": client_ip,
            "success": True
        }

        # === AWS INTEGRATIONS ===
        log_request_to_dynamodb(user_id, latency_ms, limit, success=True)
        upload_metrics_to_s3(metric_payload)
        send_latency_metric_to_cloudwatch(latency_ms)

        return {
            "user_id": user_id,
            "recommendations": recs,
            "latency_ms": Decimal(str(round(latency_ms, 2))),
            "cloud_storage": {
                "dynamodb": DDB_TABLE_NAME,
                "s3_bucket": S3_BUCKET_NAME,
                "cloudwatch_namespace": CW_NAMESPACE
            }
        }

    except Exception as e:
        success = False
        error_msg = str(e)
        logger.error(f"Error in /recommend for user {user_id}: {error_msg}")
        # Log failure to DynamoDB as well
        log_request_to_dynamodb(user_id, latency_ms=0.0, limit=limit, success=False, error_msg=error_msg)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/crash")
async def crash():
    logger.error("Manual crash triggered for failure test")
    raise RuntimeError("Simulated crash")


if __name__ == "__main__":
    import uvicorn
    print("Starting Cloud API (EC2 + DynamoDB + S3 + CloudWatch)")
    uvicorn.run(app, host="0.0.0.0", port=8000)
