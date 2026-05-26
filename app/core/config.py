import os
from pathlib import Path


def _resolve_path(value: str, *, relative_to: Path) -> Path:
    candidate = Path(os.path.expandvars(os.path.expanduser(value.strip())))
    if candidate.is_absolute():
        return candidate
    return (relative_to / candidate).resolve()


def _env_path(name: str, default: Path, *, relative_to: Path | None = None) -> Path:
    raw_value = os.getenv(name)
    if raw_value is None or not raw_value.strip():
        return default
    return _resolve_path(raw_value, relative_to=relative_to or default.parent)


def _env_float(name: str, default: float) -> float:
    raw_value = os.getenv(name)
    try:
        return float(raw_value) if raw_value is not None and str(raw_value).strip() else default
    except (TypeError, ValueError):
        return default


def _env_int(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    try:
        return int(raw_value) if raw_value is not None and str(raw_value).strip() else default
    except (TypeError, ValueError):
        return default


BASE_DIR = _env_path("AGU_BASE_DIR", Path(__file__).resolve().parents[2], relative_to=Path(__file__).resolve().parents[2].parent)
DATA_DIR = _env_path("AGU_DATA_DIR", BASE_DIR / "data", relative_to=BASE_DIR)
MODELS_DIR = _env_path("AGU_MODELS_DIR", BASE_DIR / "models", relative_to=BASE_DIR)
STATUS_DIR = _env_path("AGU_STATUS_DIR", DATA_DIR / "status", relative_to=DATA_DIR)
CACHE_DIR = _env_path("AGU_CACHE_DIR", STATUS_DIR / "cache", relative_to=STATUS_DIR)

DEFAULT_MODEL_PATH = _env_path("AGU_DEFAULT_MODEL_PATH", MODELS_DIR / "stock_ranker.pkl", relative_to=MODELS_DIR)
DEFAULT_DATA_PATH = _env_path("AGU_DEFAULT_DATA_PATH", DATA_DIR / "sample_prices.csv", relative_to=DATA_DIR)
REAL_DATA_PATH = _env_path("AGU_REAL_DATA_PATH", DATA_DIR / "a_share_prices.csv", relative_to=DATA_DIR)
REFRESH_STATUS_PATH = _env_path("AGU_REFRESH_STATUS_PATH", STATUS_DIR / "refresh_status.json", relative_to=STATUS_DIR)
REFRESH_LOG_PATH = _env_path("AGU_REFRESH_LOG_PATH", STATUS_DIR / "refresh.log", relative_to=STATUS_DIR)
MODEL_META_PATH = _env_path("AGU_MODEL_META_PATH", STATUS_DIR / "model_meta.json", relative_to=STATUS_DIR)
MARKET_OVERVIEW_CACHE_PATH = _env_path(
    "AGU_MARKET_OVERVIEW_CACHE_PATH",
    STATUS_DIR / "market_overview_cache.json",
    relative_to=STATUS_DIR,
)
HOT_NEWS_CACHE_PATH = _env_path("AGU_HOT_NEWS_CACHE_PATH", STATUS_DIR / "hot_news_cache.json", relative_to=STATUS_DIR)
STOCK_CATALOG_CACHE_PATH = _env_path("AGU_STOCK_CATALOG_CACHE_PATH", STATUS_DIR / "stock_catalog_cache.json", relative_to=STATUS_DIR)
HISTORY_CACHE_DIR = _env_path("AGU_HISTORY_CACHE_DIR", CACHE_DIR / "history", relative_to=CACHE_DIR)
DATA_HEALTH_PATH = _env_path("AGU_DATA_HEALTH_PATH", STATUS_DIR / "data_health.json", relative_to=STATUS_DIR)
DATASET_META_PATH = _env_path("AGU_DATASET_META_PATH", STATUS_DIR / "dataset_meta.json", relative_to=STATUS_DIR)
PAPER_PORTFOLIO_PATH = _env_path("AGU_PAPER_PORTFOLIO_PATH", DATA_DIR / "paper_portfolio.json", relative_to=DATA_DIR)
APP_PORT = _env_int("AGU_APP_PORT", 8000)
PORTFOLIO_DEFAULT_CASH = _env_float("AGU_PORTFOLIO_DEFAULT_CASH", 1_000_000.0)

DEFAULT_SAMPLE_SYMBOLS: list[tuple[str, str]] = [
    ("600519", "贵州茅台"),
    ("000333", "美的集团"),
    ("600036", "招商银行"),
    ("000651", "格力电器"),
    ("601318", "中国平安"),
    ("002415", "海康威视"),
    ("300750", "宁德时代"),
    ("600276", "恒瑞医药"),
    ("002594", "比亚迪"),
    ("600887", "伊利股份"),
]

INDEX_POOLS: dict[str, dict[str, str]] = {
    "hs300": {"symbol": "000300", "name": "沪深300"},
    "zz500": {"symbol": "000905", "name": "中证500"},
}
