"""
Evaluate SVD recommendation model accuracy using the historical rating data.

- Uses Surprise SVD (same library as precompute_recommendations.py)
- Reads ../data/processed/interactions_filtered.csv
- Runs k-fold cross-validation and prints RMSE & MAE
"""

import os
import pandas as pd
from surprise import SVD, Dataset, Reader
from surprise.model_selection import cross_validate


# ---------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------

# Path to your full interactions dataset
INTERACTIONS_CSV = "../data/processed/interactions_filtered.csv"

# Rating scale for Amazon reviews (adjust if your data differs)
RATING_MIN = 1.0
RATING_MAX = 5.0

# Number of cross-validation folds
N_FOLDS = 3


def load_interactions(csv_path: str) -> pd.DataFrame:
    """
    Load the interactions CSV into a pandas DataFrame.
    Expecting columns: user_id, item_id, rating, timestamp
    (same format as interactions_filtered.csv).
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Interactions CSV not found at: {csv_path}")

    df = pd.read_csv(csv_path)

    # Show original columns (optional debug)
    print("Original columns:", df.columns.tolist())

    # Normalize column names (strip + lower)
    df.columns = [c.strip() for c in df.columns]

    # Map your actual names -> the ones the rest of the code expects
    rename_map = {
        "User_ID": "user_id",
        "Product_ID": "item_id",
        "Rating": "rating",
        "Timestamp": "timestamp",
    }
    df = df.rename(columns=rename_map)
    
    # Basic sanity check
    expected_cols = {"user_id", "item_id", "rating"}
    if not expected_cols.issubset(df.columns):
        raise ValueError(
            f"Expected columns {expected_cols}, but got {df.columns.tolist()}"
        )

    print(f"Loaded interactions: {len(df)} rows from {csv_path}")
    print(f"Unique users: {df['user_id'].nunique()}, unique items: {df['item_id'].nunique()}")
    return df


def build_surprise_dataset(df: pd.DataFrame) -> Dataset:
    """
    Build Surprise Dataset from a DataFrame with user_id, item_id, rating.
    """
    reader = Reader(rating_scale=(RATING_MIN, RATING_MAX))
    data = Dataset.load_from_df(df[["user_id", "item_id", "rating"]], reader)
    return data


def evaluate_svd(data: Dataset, n_folds: int = 3):
    """
    Run cross-validation for SVD and print RMSE/MAE.
    """
    algo = SVD(
        n_factors=50,   # match your precompute_recommendations.py settings if needed
        n_epochs=20,
        biased=True
    )

    print("\n=== Running cross-validation for SVD ===")
    results = cross_validate(
        algo,
        data,
        measures=["RMSE", "MAE"],
        cv=n_folds,
        verbose=True
    )

    # Aggregate metrics
    rmse_scores = results["test_rmse"]
    mae_scores = results["test_mae"]

    print("\n=== Summary ===")
    print(f"Folds: {n_folds}")
    print(f"RMSE per fold: {[round(x, 4) for x in rmse_scores]}")
    print(f"MAE  per fold: {[round(x, 4) for x in mae_scores]}")
    print(f"Avg RMSE: {sum(rmse_scores)/len(rmse_scores):.4f}")
    print(f"Avg MAE:  {sum(mae_scores)/len(mae_scores):.4f}")


def main():
    df = load_interactions(INTERACTIONS_CSV)
    data = build_surprise_dataset(df)
    evaluate_svd(data, n_folds=N_FOLDS)


if __name__ == "__main__":
    main()