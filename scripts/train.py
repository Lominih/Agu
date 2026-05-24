from pathlib import Path
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.core.config import DEFAULT_DATA_PATH, DEFAULT_MODEL_PATH
from app.services.dataset import build_features, load_price_data
from app.services.modeling import train_model


def main() -> None:
    prices = load_price_data(DEFAULT_DATA_PATH)
    features = build_features(prices)
    metrics = train_model(features, DEFAULT_MODEL_PATH)
    print("训练完成")
    print(metrics)


if __name__ == "__main__":
    main()
