from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
DEFAULT_MODEL_PATH = MODELS_DIR / "stock_ranker.pkl"
DEFAULT_DATA_PATH = DATA_DIR / "sample_prices.csv"

