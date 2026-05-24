from pathlib import Path
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.core.config import DEFAULT_MODEL_PATH, DEFAULT_DATA_PATH, REAL_DATA_PATH  # noqa: E402
from app.services.dataset import build_features, load_price_data  # noqa: E402
from app.services.modeling import train_model  # noqa: E402


def main() -> None:
    source = "real" if REAL_DATA_PATH.exists() else "sample"
    data_path = REAL_DATA_PATH if source == "real" else DEFAULT_DATA_PATH

    prices = load_price_data(data_path, source=source, allow_remote_fetch=False)
    features = build_features(prices)
    metrics = train_model(features, DEFAULT_MODEL_PATH)

    print(f"训练完成，当前数据来源: {source}")
    print(metrics)


if __name__ == "__main__":
    main()
