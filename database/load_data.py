import psycopg2
from psycopg2.extras import execute_batch
import csv
import os
from typing import List, Tuple

DB_CONFIG = {
    "host": "localhost",
    "database": "recommendations",
    "user": "s4p"
}

CSV_PATHS = {
    "users": "../data/processed/users_top10k.csv",
    "items": "../data/processed/items_metadata.csv",
    "interactions": "../data/processed/interactions_filtered.csv",
    #"users": "../data/processed/users_sample10.csv",
    #"items": "../data/processed/sample_items_metadata.csv",
    #"interactions": "../data/processed/interactions_sample.csv",
}

BATCH_SIZE = 10000

def get_db_connection():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False  # Use transactions for robust batch loading
        print("Database connection successful.")
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def load_csv_data_chunks(file_path: str):
    if not os.path.exists(file_path):
        print(f"Current working directory: {os.getcwd()}")
        raise FileNotFoundError(f"CSV file not found at: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)

        data_chunk = []
        for row in reader:
            data_chunk.append(tuple(row))

            if len(data_chunk) >= BATCH_SIZE:
                yield data_chunk
                data_chunk = []

        if data_chunk:
            yield data_chunk

def load_users(conn):
    print(f"\n Loading users from: {CSV_PATHS['users']}...")
    sql = "INSERT INTO users (user_id) VALUES (%s) ON CONFLICT (user_id) DO NOTHING"
    count = 0
    try:
        with conn.cursor() as cur:
            for chunk in load_csv_data_chunks(CSV_PATHS['users']):
                casted_chunk = [(row[0],) for row in chunk]
                execute_batch(cur, sql, casted_chunk, page_size=BATCH_SIZE)
                count += len(casted_chunk)
        conn.commit()
        print(f"Successfully loaded {count} rows into 'users' table.")
        return count
    except Exception as e:
        conn.rollback()
        print(f"Error loading users: {e}")
        return 0

def load_items(conn):
    print(f"\n Loading items from: {CSV_PATHS['items']}...")
    sql = "INSERT INTO items (item_id) VALUES (%s) ON CONFLICT (item_id) DO NOTHING"
    count = 0
    try:
        with conn.cursor() as cur:
            for chunk in load_csv_data_chunks(CSV_PATHS['items']):
                casted_chunk = [(row[0],) for row in chunk]
                execute_batch(cur, sql, casted_chunk, page_size=BATCH_SIZE)
                count += len(casted_chunk)
        conn.commit()
        print(f" Successfully loaded {count} rows into 'items' table.")
        return count
    except Exception as e:
        conn.rollback()
        print(f" Error loading items: {e}")
        return 0

def load_interactions(conn):
    print(f"\n Loading interactions from: {CSV_PATHS['interactions']}...")
    sql = "INSERT INTO interactions (user_id, item_id, rating, timestamp) VALUES (%s, %s, %s, %s)"
    count = 0

    try:
        with conn.cursor() as cur:
            for chunk in load_csv_data_chunks(CSV_PATHS['interactions']):
                casted_chunk = [
                    (
                        row[0],
                        row[1],
                        float(row[2]),
                        int(row[3])
                    )
                    for row in chunk
                ]
                execute_batch(cur, sql, casted_chunk, page_size=BATCH_SIZE)
                count += len(casted_chunk)
        conn.commit()
        print(f" Successfully loaded {count} rows into 'interactions' table.")
        return count
    except Exception as e:
        conn.rollback()
        print(f" Error loading interactions: {e}")
        return 0

def verify_data_load(conn, loaded_counts: dict):
    print("\n--- Verification and Sanity Checks ---")

    table_counts = {}
    with conn.cursor() as cur:
        for table in ['users', 'items', 'interactions']:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            table_counts[table] = count
            print(f"Database count for '{table}': {count} rows.")

    print("\nSanity Check 1: Comparing loaded vs. DB counts:")
    for table, db_count in table_counts.items():
        if db_count == loaded_counts.get(table, 0):
            print(f"  [PASS] {table}: Loaded count matches DB count.")
        else:
            print(
                f"  [FAIL] {table}: Loaded {loaded_counts.get(table, 0)} but DB has {db_count}. (Check for data duplication/missing rows)")


def main():
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return

        with conn.cursor() as cur:
            print("Clearing tables before load...")

            cur.execute("""
                TRUNCATE TABLE interactions RESTART IDENTITY CASCADE;
                TRUNCATE TABLE items RESTART IDENTITY CASCADE;
                TRUNCATE TABLE users RESTART IDENTITY CASCADE;
            """)

        conn.commit()
        print("Tables truncated. Starting fresh load.\n")

        loaded_counts = {}

        # 1. Load users
        loaded_counts['users'] = load_users(conn)

        # 2. Load items
        loaded_counts['items'] = load_items(conn)

        # 3. Load interactions
        loaded_counts['interactions'] = load_interactions(conn)

        # 4. Verify and check
        verify_data_load(conn, loaded_counts)

        # 5. Skip recommendations table load
        print("\nNote: Skipping 'recommendations' table load as no CSV path was provided.")


    except Exception as e:
        print(f"\n An unexpected error occurred during execution: {e}")
        if conn and not conn.closed:
            conn.rollback()
    finally:
        if conn and not conn.closed:
            conn.close()
            print("\nDatabase connection closed.")


if __name__ == "__main__":
    main()