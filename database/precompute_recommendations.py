import psycopg2
from psycopg2.extras import execute_batch
import pandas as pd
from surprise import SVD, Dataset, Reader
from surprise.model_selection import train_test_split
import time
import json
import pickle
import os
from typing import List, Dict, Any


DB_CONFIG = {
    "host": "localhost",
    "database": "recommendations",
    "user": "s4p",
}

MODEL_PATH = "../data/models/svd_model.pkl"
TOP_N = 20
BATCH_SIZE = 10000


def get_db_connection():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False
        return conn
    except Exception as e:
        print(f" Error connecting to database: {e}")
        return None


def load_interaction_data(conn) -> pd.DataFrame:
    print(" Loading interaction data from PostgreSQL...")
    sql = "SELECT user_id, item_id, rating FROM interactions"

    start_time = time.time()
    try:
        df = pd.read_sql(sql, conn)
        load_time = time.time() - start_time
        print(f" Loaded {len(df)} interactions into DataFrame in {load_time:.2f} seconds.")
        return df
    except Exception as e:
        print(f" Error loading interaction data: {e}")
        return pd.DataFrame()


def train_and_save_model(df: pd.DataFrame, model_path: str):
    print("\n Preparing dataset and training SVD model...")

    reader = Reader(rating_scale=(df['rating'].min(), df['rating'].max()))
    data = Dataset.load_from_df(df[['user_id', 'item_id', 'rating']], reader)
    trainset = data.build_full_trainset()

    start_time = time.time()
    model = SVD(n_factors=50, n_epochs=20, random_state=42, verbose=False)
    model.fit(trainset)
    training_time = time.time() - start_time

    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)

    print(f" SVD model trained and saved to {model_path}")
    print(f" Training Time: {training_time:.2f} seconds")
    return model, trainset, training_time

def get_recommendations_for_all_users(model, trainset, all_item_ids: set, num_recommendations: int) -> Dict[
    str, List[Dict[str, Any]]]:
    print("\nGenerating recommendations for all users...")

    user_ids = [trainset.to_raw_uid(u) for u in trainset.all_users()]
    known_interactions = {
        trainset.to_raw_uid(u): set(trainset.to_raw_iid(i) for (i, r) in trainset.ur[u])
        for u in trainset.all_users()
    }

    all_recommendations = {}
    total_users = len(user_ids)

    start_time = time.time()

    for i, user_inner_id in enumerate(trainset.all_users()):
        user_id = trainset.to_raw_uid(user_inner_id)

    # for i, user_id in enumerate(user_ids):
        known_items = known_interactions.get(user_id, set())
        items_to_predict = list(all_item_ids - known_items)
        # predictions = [
        #     model.predict(user_id, item_id)
        predictions = [
            model.predict(user_inner_id, item_id)  # Use inner ID for predict
            for item_id in items_to_predict
        ]

        predictions.sort(key=lambda x: x.est, reverse=True)
        top_n = [
            {"item_id": p.iid, "score": round(p.est, 4)}
            for p in predictions[:num_recommendations]
        ]

        all_recommendations[user_id] = top_n

        if (i + 1) % 1000 == 0:
            print(f"   Processed {i + 1}/{total_users} users...")

    computation_time = time.time() - start_time
    print(f"Recommendation computation complete.")
    print(f"Computation Time: {computation_time:.2f} seconds")
    return all_recommendations, computation_time


def store_recommendations(conn, recommendations_data: Dict[str, List[Dict[str, Any]]]) -> int:
    print("\nStoring recommendations in PostgreSQL...")
    sql = """
    INSERT INTO recommendations (user_id, recommended_items)
    VALUES (%s, %s::JSONB)
    ON CONFLICT (user_id) DO UPDATE
    SET recommended_items = EXCLUDED.recommended_items,
        computed_at = NOW()
    """
    count = 0
    start_time = time.time()

    try:
        batch_data = [
            (user_id, json.dumps(recs))
            for user_id, recs in recommendations_data.items()
        ]

        with conn.cursor() as cur:
            execute_batch(cur, sql, batch_data, page_size=BATCH_SIZE)
            count = len(batch_data)

        conn.commit()
        storage_time = time.time() - start_time
        print(f"Successfully stored {count} recommendation lists.")
        print(f"Storage Time: {storage_time:.2f} seconds")
        return count
    except Exception as e:
        conn.rollback()
        print(f"Error storing recommendations: {e}")
        return 0

def main():
    conn = get_db_connection()
    if conn is None:
        print("Exiting due to database connection failure.")
        return
    try:
        interactions_df = load_interaction_data(conn)
        if interactions_df.empty:
            return

        all_item_ids = set(interactions_df['item_id'].unique())
        print(f"Total unique items: {len(all_item_ids)}")

        model, trainset, training_time = train_and_save_model(interactions_df, MODEL_PATH)
        recommendations, computation_time = get_recommendations_for_all_users(
            model, trainset, all_item_ids, TOP_N
        )
        stored_count = store_recommendations(conn, recommendations)

        print("\n=============================================")
        print("✨ Recommendation Precomputation Complete ✨")
        print("=============================================")
        print(f"Model: SVD (Factors: 50, Epochs: 20)")
        print(f"Total Users Processed: {stored_count} (Top {TOP_N} recommendations each)")
        print(f"Total Time Breakdown:")
        print(f"  - Training Time:       {training_time:.2f} seconds")
        print(f"  - Computation Time:    {computation_time:.2f} seconds")

        print("\n--- Sample Recommendations ---")
        sample_users = list(recommendations.keys())[:5]
        for user_id in sample_users:
            recs = recommendations[user_id]
            print(f"\nUser ID: {user_id}")
            print("  Top 3 Items:")
            for i, rec in enumerate(recs[:3]):
                print(f"    {i + 1}. Item {rec['item_id']} (Predicted Score: {rec['score']})")

    except Exception as e:
        print(f"\nAn unexpected error occurred in main execution: {e}")
        conn.rollback()
    finally:
        if conn and not conn.closed:
            conn.close()
            print("\nDatabase connection closed.")


if __name__ == "__main__":
    main()