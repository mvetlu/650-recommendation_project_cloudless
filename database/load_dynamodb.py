import boto3
import csv
import json
import time
from decimal import Decimal
from botocore.exceptions import ClientError

# ============================================================================
# CONFIGURATION - EDIT THIS SECTION TO SWITCH BETWEEN 10 AND 10K USERS
# ============================================================================

# Dataset size selection
DATASET_SIZE = "10k"  # Change to "10k" when ready for full dataset

# CSV paths based on dataset size
if DATASET_SIZE == "10":
    CSV_PATHS = {
        "users": "../data/processed/users_sample10.csv",  # Your 10-user test file
        "items": "../data/processed/sample_items_metadata.csv",
        "interactions": "../data/processed/interactions_sample.csv",
        "recommendations": "../data/models/recommendations_export.csv"  # Export from PostgreSQL first
    }
elif DATASET_SIZE == "10k":
    CSV_PATHS = {
        "users": "../data/processed/users_top10k.csv",  # Your full 10K file
        "items": "../data/processed/items_metadata.csv",
        "interactions": "../data/processed/interactions_filtered.csv",
        "recommendations": "../data/models/recommendations_export.csv"
    }

# DynamoDB table names
DYNAMODB_TABLES = {
    "users": "rec-users",
    "items": "rec-items",
    "interactions": "rec-interactions",
    "recommendations": "rec-recommendations"
}

# Batch size for DynamoDB batch writes (max 25)
BATCH_SIZE = 25

# AWS region
AWS_REGION = "us-east-1"  # Change to your preferred region


# ============================================================================
# END CONFIGURATION
# ============================================================================


def get_dynamodb_client():
    """Initialize DynamoDB client"""
    return boto3.client('dynamodb', region_name=AWS_REGION)


def get_dynamodb_resource():
    """Initialize DynamoDB resource"""
    return boto3.resource('dynamodb', region_name=AWS_REGION)


def convert_to_decimal(value):
    """Convert float to Decimal for DynamoDB"""
    if isinstance(value, float):
        return Decimal(str(value))
    return value


def load_users(dynamodb, csv_path, table_name):
    """Load users into DynamoDB"""
    print(f"\n{'=' * 70}")
    print(f"Loading USERS from: {csv_path}")
    print(f"Target table: {table_name}")
    print(f"{'=' * 70}")

    table = dynamodb.Table(table_name)
    count = 0
    batch = []

    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header

            for row in reader:
                user_id = row[0]

                item = {
                    'user_id': user_id
                }

                batch.append({'PutRequest': {'Item': item}})

                if len(batch) >= BATCH_SIZE:
                    table.meta.client.batch_write_item(
                        RequestItems={table_name: batch}
                    )
                    count += len(batch)
                    print(f"  Loaded {count} users...")
                    batch = []
                    time.sleep(0.1)  # Avoid throttling

            # Write remaining items
            if batch:
                table.meta.client.batch_write_item(
                    RequestItems={table_name: batch}
                )
                count += len(batch)

        print(f"✅ Successfully loaded {count} users")
        return count

    except Exception as e:
        print(f"❌ Error loading users: {e}")
        return 0


def load_items(dynamodb, csv_path, table_name):
    """Load items into DynamoDB"""
    print(f"\n{'=' * 70}")
    print(f"Loading ITEMS from: {csv_path}")
    print(f"Target table: {table_name}")
    print(f"{'=' * 70}")

    table = dynamodb.Table(table_name)
    count = 0
    batch = []

    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header

            for row in reader:
                item_id = row[0]

                item = {
                    'item_id': item_id
                }

                batch.append({'PutRequest': {'Item': item}})

                if len(batch) >= BATCH_SIZE:
                    table.meta.client.batch_write_item(
                        RequestItems={table_name: batch}
                    )
                    count += len(batch)
                    print(f"  Loaded {count} items...")
                    batch = []
                    time.sleep(0.1)

            if batch:
                table.meta.client.batch_write_item(
                    RequestItems={table_name: batch}
                )
                count += len(batch)

        print(f"✅ Successfully loaded {count} items")
        return count

    except Exception as e:
        print(f"❌ Error loading items: {e}")
        return 0


def load_interactions(dynamodb, csv_path, table_name):
    """Load interactions into DynamoDB"""
    print(f"\n{'=' * 70}")
    print(f"Loading INTERACTIONS from: {csv_path}")
    print(f"Target table: {table_name}")
    print(f"{'=' * 70}")

    table = dynamodb.Table(table_name)
    count = 0
    batch = []

    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header

            for row in reader:
                user_id = row[0]
                item_id = row[1]
                rating = convert_to_decimal(float(row[2]))
                timestamp = int(row[3])

                # Create unique interaction_id as composite key
                interaction_id = f"{timestamp}#{item_id}"

                item = {
                    'user_id': user_id,
                    'interaction_id': interaction_id,  # New sort key
                    'item_id': item_id,
                    'rating': rating,
                    'timestamp': timestamp  # Keep for querying
                }

                batch.append({'PutRequest': {'Item': item}})

                if len(batch) >= BATCH_SIZE:
                    table.meta.client.batch_write_item(
                        RequestItems={table_name: batch}
                    )
                    count += len(batch)
                    print(f"  Loaded {count} interactions...")
                    batch = []
                    time.sleep(0.1)

            if batch:
                table.meta.client.batch_write_item(
                    RequestItems={table_name: batch}
                )
                count += len(batch)

        print(f"✅ Successfully loaded {count} interactions")
        return count

    except Exception as e:
        print(f"❌ Error loading interactions: {e}")
        return 0


def export_recommendations_from_postgres():
    """
    Export recommendations from PostgreSQL to CSV
    Run this first if you haven't already
    """
    print("\n{'='*70}")
    print("EXPORTING RECOMMENDATIONS FROM POSTGRESQL")
    print(f"{'=' * 70}")

    import psycopg2
    import os

    DB_CONFIG = {
        "host": "localhost",
        "database": "recommendations",
        "user": os.environ.get("DB_USER", "postgres")
    }

    output_path = "../data/models/recommendations_export.csv"

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        query = "SELECT user_id, recommended_items FROM recommendations"
        cursor.execute(query)

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['user_id', 'recommended_items'])

            for row in cursor.fetchall():
                user_id = row[0]
                recommended_items = json.dumps(row[1])  # JSONB to JSON string
                writer.writerow([user_id, recommended_items])

        cursor.close()
        conn.close()

        print(f"✅ Exported recommendations to: {output_path}")
        return True

    except Exception as e:
        print(f"❌ Error exporting recommendations: {e}")
        return False


def load_recommendations(dynamodb, csv_path, table_name):
    """Load recommendations into DynamoDB"""
    print(f"\n{'=' * 70}")
    print(f"Loading RECOMMENDATIONS from: {csv_path}")
    print(f"Target table: {table_name}")
    print(f"{'=' * 70}")

    table = dynamodb.Table(table_name)
    count = 0
    batch = []

    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header

            for row in reader:
                user_id = row[0]
                recommended_items_json = row[1]

                # Parse JSON and convert floats to Decimals
                recommended_items = json.loads(recommended_items_json)
                for rec in recommended_items:
                    rec['score'] = convert_to_decimal(rec['score'])

                item = {
                    'user_id': user_id,
                    'recommended_items': recommended_items
                }

                batch.append({'PutRequest': {'Item': item}})

                if len(batch) >= BATCH_SIZE:
                    table.meta.client.batch_write_item(
                        RequestItems={table_name: batch}
                    )
                    count += len(batch)
                    print(f"  Loaded {count} recommendation lists...")
                    batch = []
                    time.sleep(0.1)

            if batch:
                table.meta.client.batch_write_item(
                    RequestItems={table_name: batch}
                )
                count += len(batch)

        print(f"✅ Successfully loaded {count} recommendation lists")
        return count

    except Exception as e:
        print(f"❌ Error loading recommendations: {e}")
        return 0


def verify_tables(dynamodb):
    """Verify data was loaded correctly"""
    print(f"\n{'=' * 70}")
    print("VERIFICATION")
    print(f"{'=' * 70}")

    client = boto3.client('dynamodb', region_name=AWS_REGION)

    for key, table_name in DYNAMODB_TABLES.items():
        try:
            response = client.describe_table(TableName=table_name)
            item_count = response['Table']['ItemCount']
            print(f"  {table_name}: {item_count} items")
        except Exception as e:
            print(f"  {table_name}: Error - {e}")


def main():
    print("\n" + "=" * 70)
    print("DYNAMODB DATA LOADER")
    print("=" * 70)
    print(f"Dataset size: {DATASET_SIZE}")
    print(f"AWS Region: {AWS_REGION}")
    print("=" * 70)

    # Initialize DynamoDB
    dynamodb = get_dynamodb_resource()

    # Step 1: Export recommendations from PostgreSQL (if not done)
    print("\nStep 1: Export recommendations from PostgreSQL")
    print("Have you already exported? (y/n)")
    export_choice = input().strip().lower()

    if export_choice != 'y':
        export_recommendations_from_postgres()

    # Step 2: Load data
    loaded_counts = {}

    print("\nStep 2: Load data into DynamoDB")

    loaded_counts['users'] = load_users(
        dynamodb,
        CSV_PATHS['users'],
        DYNAMODB_TABLES['users']
    )

    loaded_counts['items'] = load_items(
        dynamodb,
        CSV_PATHS['items'],
        DYNAMODB_TABLES['items']
    )

    loaded_counts['interactions'] = load_interactions(
        dynamodb,
        CSV_PATHS['interactions'],
        DYNAMODB_TABLES['interactions']
    )

    loaded_counts['recommendations'] = load_recommendations(
        dynamodb,
        CSV_PATHS['recommendations'],
        DYNAMODB_TABLES['recommendations']
    )

    # Step 3: Verify
    print("\nStep 3: Verify data")
    verify_tables(dynamodb)

    print("\n" + "=" * 70)
    print("✅ DATA LOADING COMPLETE")
    print("=" * 70)
    print(f"Users: {loaded_counts['users']}")
    print(f"Items: {loaded_counts['items']}")
    print(f"Interactions: {loaded_counts['interactions']}")
    print(f"Recommendations: {loaded_counts['recommendations']}")
    print("=" * 70)


if __name__ == "__main__":
    main()