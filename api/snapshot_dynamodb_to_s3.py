import os
import json
import time

import boto3
from botocore.exceptions import ClientError


# ---------------- CONFIG ----------------

# DynamoDB region
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

# Table that holds precomputed recommendations
DYNAMO_RECOMMENDATIONS_TABLE = os.environ.get(
    "DYNAMO_RECOMMENDATIONS_TABLE",
    "rec-recommendations"  # default from your dynamodb.py config
)

# S3 bucket where snapshot will be stored
RESULTS_BUCKET = os.environ.get("RESULTS_BUCKET", "d650-emily-test-bucket")

# S3 prefix (folder) where we place snapshots
SNAPSHOT_PREFIX = os.environ.get("SNAPSHOT_PREFIX", "snapshots")

# ----------------------------------------


def get_dynamodb_table():
    """Return a DynamoDB Table resource for the recommendations table."""
    dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
    return dynamodb.Table(DYNAMO_RECOMMENDATIONS_TABLE)


def scan_entire_table(table):
    """
    Scan the entire DynamoDB table, handling pagination.
    Returns a list of all items.
    """
    print(f"Scanning DynamoDB table: {DYNAMO_RECOMMENDATIONS_TABLE} in {AWS_REGION}...")
    items = []
    scan_kwargs = {}
    while True:
        response = table.scan(**scan_kwargs)
        batch = response.get("Items", [])
        items.extend(batch)
        print(f"  Retrieved {len(batch)} items (total so far: {len(items)})")

        # Pagination
        last_key = response.get("LastEvaluatedKey")
        if not last_key:
            break
        scan_kwargs["ExclusiveStartKey"] = last_key

    print(f" Scan complete. Total items: {len(items)}")
    return items


def upload_snapshot_to_s3(items):
    """
    Upload the items list as pretty JSON to S3.
    """
    s3 = boto3.client("s3")

    # e.g. snapshots/rec_recommendations_20251206T205501.json
    timestamp = time.strftime("%Y%m%dT%H%M%S")
    key = f"{SNAPSHOT_PREFIX}/rec_recommendations_{timestamp}.json"

    body = json.dumps(items, indent=2, default=str)

    print(f"Uploading snapshot to s3://{RESULTS_BUCKET}/{key} ...")
    s3.put_object(
        Bucket=RESULTS_BUCKET,
        Key=key,
        Body=body.encode("utf-8"),
        ContentType="application/json"
    )
    print("Upload complete.")


def main():
    print("=" * 70)
    print("DYNAMODB → S3 RECOMMENDATIONS SNAPSHOT")
    print("=" * 70)
    print(f"AWS Region: {AWS_REGION}")
    print(f"DynamoDB table: {DYNAMO_RECOMMENDATIONS_TABLE}")
    print(f"S3 bucket: {RESULTS_BUCKET}")
    print(f"S3 prefix: {SNAPSHOT_PREFIX}")
    print("=" * 70)

    # 1. Connect to table
    try:
        table = get_dynamodb_table()
    except ClientError as e:
        print(f" Error getting DynamoDB table: {e}")
        return

    # 2. Scan all items
    try:
        items = scan_entire_table(table)
    except ClientError as e:
        print(f" Error scanning table: {e}")
        return

    if not items:
        print("  No items found in table; nothing to snapshot.")
        return

    # 3. Upload snapshot to S3
    try:
        upload_snapshot_to_s3(items)
    except ClientError as e:
        print(f" Error uploading snapshot to S3: {e}")
        return

    print("=" * 70)
    print(" DYNAMODB RECOMMENDATIONS SNAPSHOT COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()