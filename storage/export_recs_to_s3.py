"""
Export the precomputed recommendations from local PostgreSQL to S3 on the cloud solution.
Postgres table -> one json per user in s3

Assumptions:
(1) psql is running on localhost (noncloud solution)
(2) db name 'recommendations'
(3) table: 'recommendations(user_id, recommended_items, computed_at)'
(4) AWS credentials are configured 
(5) In environment before running, set RESULTS_BUCKET

Usage:
1. set s3 bucket name
2. connect to local postgresql 
3. count rows in recommendations table
4. iterate through all rows in batches of 1000
5. log progress every 100 users
6. close the DB connection and print final summary 


"""
#################### --- ENVIRONMENT SET UP ---#################################
import os 
import json
import psycopg2
from psycopg2.extras import RealDictCursor
import boto3
from datetime import datetime, timezone

#################### --- DB CONFIG: mirrors app.py ---#################################
DB_CONFIG = {
    "host": "localhost",
    "database": "recommendations",
    "user": "s4p",
    "password": os.getenv("DB_PASSWORD", ""),
}

#################### --- S3 CONFIG ---#################################
# Name s3 bucket
RESULTS_BUCKET = os.getenv("RESULTS_BUCKET")  
S3_PREFIX = os.getenv("RESULTS_PREFIX", "recommendations/")  

# Create S3 client with AWS credentials
s3 = boto3.client("s3")

"""
Open Posetgres connection using DB_CONFIG

Success: returns a live connection object
failure: wraps the error in RuntimeError 
"""
def get_db_connection():
    try:
        conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        raise RuntimeError(f"Failed to connect to Postgres: {e}")


"""
Ensure consistent python structure from columns
"""
def normalize_recommended_items(raw):
    """
    Ensure recommended_items is a Python list/dict.
    Handles JSONB or text-encoded JSON from Postgres.
    """
    if raw is None:
        return []

    # Already a Python list/dict from psycopg2 + JSONB
    if isinstance(raw, (list, dict)):
        return raw

    # If it's a string, try to json.loads it
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            # fall back to wrapping it as-is
            return {"raw": raw}

    # Fallback: wrap in a dict for safety
    return {"value": raw}

"""
Exporter
1. check s3 config 
2. connect to DB 
3. Get total count for progress
4. select all recommendations 
5. batch fetch loop
6. per-row processing (inside loop)
7. derive s3 key/path
8. upload to s3
9. progress logging
10. clean up and close 
"""
def export_recommendations_to_s3():
    if not RESULTS_BUCKET:
        raise RuntimeError(
            "RESULTS_BUCKET environment variable is not set. "
            "Set it to your S3 bucket name before running."
        )

    conn = get_db_connection()
    cur = conn.cursor()

    # Count first, just for progress info
    cur.execute("SELECT COUNT(*) AS count FROM recommendations;")
    total = cur.fetchone()["count"]
    print(f"Found {total} rows in 'recommendations' table.")

    # Stream rows to avoid loading everything in memory at once
    cur.execute("SELECT user_id, recommended_items, computed_at FROM recommendations;")

    exported = 0
    batch_size = 1000

    while True:
        rows = cur.fetchmany(batch_size)
        if not rows:
            break

        for row in rows:
            user_id = row["user_id"]
            raw_recs = row["recommended_items"]
            computed_at = row["computed_at"]

            recs = normalize_recommended_items(raw_recs)

            payload = {
                "user_id": user_id,
                "recommendations": recs,
                "computed_at": computed_at.isoformat() if computed_at else None,
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "source": "non-cloud-postgres",
            }

            key = f"{S3_PREFIX.rstrip('/')}/{user_id}.json"

            s3.put_object(
                Bucket=RESULTS_BUCKET,
                Key=key,
                Body=json.dumps(payload),
                ContentType="application/json",
            )

            exported += 1
            if exported % 100 == 0:
                print(f"Exported {exported}/{total} users...")

    cur.close()
    conn.close()

    print(
        f"Done. Exported {exported} users' recommendations to "
        f"s3://{RESULTS_BUCKET}/{S3_PREFIX}"
    )


if __name__ == "__main__":
    print("Starting export of recommendations to S3...")
    export_recommendations_to_s3()