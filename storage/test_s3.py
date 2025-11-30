# storage test script makes dummy data to export to S3 bucket 
# storage/test_s3.py
import os
import json
import boto3

RESULTS_BUCKET = os.getenv("RESULTS_BUCKET_test")

if not RESULTS_BUCKET:
    raise RuntimeError("Set RESULTS_BUCKET_test env var first")

s3 = boto3.client("s3")

def main():
    payload = {
        "test": True,
        "message": "hello from emily's laptop",
    }

    key = "test/test-object.json"

    s3.put_object(
        Bucket=RESULTS_BUCKET,
        Key=key,
        Body=json.dumps(payload),
        ContentType="application/json",
    )

    print(f"Wrote test object to s3://{RESULTS_BUCKET}/{key}")

if __name__ == "__main__":
    main()
