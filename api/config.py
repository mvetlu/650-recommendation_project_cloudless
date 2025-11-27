import os
from typing import Dict, Any

class BaseConfig:
    # 1. Database Connection Settings
    # Reads password from environment variable for security
    DB_HOST: str = "localhost"
    DB_NAME: str = "recommendations"
    DB_USER: str = "s4p"
    # Use os.getenv() here, but the actual retrieval is handled in app.py
    DB_PASSWORD: str = os.getenv('DB_PASSWORD', '')

    DB_CONFIG: Dict[str, str] = {
        'host': DB_HOST,
        'database': DB_NAME,
        'user': DB_USER,
        'password': DB_PASSWORD
    }

    # 2. API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_WORKERS: int = 1 # Overridden in Production

    # 3. Model/Recommendation Settings
    # Maximum number of recommendations to return
    TOP_N_LIMIT: int = 20
    # Default limit for the API endpoint
    DEFAULT_RECOMMENDATION_LIMIT: int = 10

    # 4. Base File Paths
    # Define a base path if needed, or define specific paths below.
    DATA_BASE_PATH: str = "../data/processed"

    # 5. Environment-Specific Settings
    ENVIRONMENT: str = "BASE"


class TestingConfig(BaseConfig):
    """Configuration for a small-scale testing environment (10 users)."""
    ENVIRONMENT: str = "TESTING"

    # 2. API Configuration (Testing uses a different port for safety)
    API_PORT: int = 8001
    API_WORKERS: int = 1 # Single process for easy debugging

    # 4. File Paths (Using the small sample files)
    CSV_PATHS: Dict[str, str] = {
        "users": os.path.join(BaseConfig.DATA_BASE_PATH, "users_sample10.csv"),
        "items": os.path.join(BaseConfig.DATA_BASE_PATH, "sample_items_metadata.csv"),
        "interactions": os.path.join(BaseConfig.DATA_BASE_PATH, "interactions_sample.csv"),
    }

class ProductionConfig(BaseConfig):
    """Configuration for the production environment (10K users)."""
    ENVIRONMENT: str = "PRODUCTION"

    # 2. API Configuration (Optimized for performance)
    API_PORT: int = 8000
    API_WORKERS: int = 4 # Use multiple workers for concurrency

    # 4. File Paths (Using the full dataset files)
    CSV_PATHS: Dict[str, str] = {
        "users": os.path.join(BaseConfig.DATA_BASE_PATH, "users_top10k.csv"),
        "items": os.path.join(BaseConfig.DATA_BASE_PATH, "items_metadata.csv"),
        "interactions": os.path.join(BaseConfig.DATA_BASE_PATH, "interactions_filtered.csv"),
    }


# Determine which config to load based on an environment variable.
def get_config(env: str = None):
    """Returns the appropriate configuration class based on the environment."""
    env = env or os.getenv("APP_ENV", "TESTING").upper()

    if env == "PRODUCTION":
        return ProductionConfig
    # Default to Testing if APP_ENV is not set or unrecognized
    return TestingConfig

# The active configuration object used by the application
Config = get_config()