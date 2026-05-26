from __future__ import annotations

import importlib
import os
from pathlib import Path
import unittest


CONFIG_ENV_KEYS = [
    "AGU_BASE_DIR",
    "AGU_DATA_DIR",
    "AGU_MODELS_DIR",
    "AGU_STATUS_DIR",
    "AGU_CACHE_DIR",
    "AGU_DEFAULT_MODEL_PATH",
    "AGU_DEFAULT_DATA_PATH",
    "AGU_REAL_DATA_PATH",
    "AGU_REFRESH_STATUS_PATH",
    "AGU_REFRESH_LOG_PATH",
    "AGU_MODEL_META_PATH",
    "AGU_MARKET_OVERVIEW_CACHE_PATH",
    "AGU_HOT_NEWS_CACHE_PATH",
    "AGU_STOCK_CATALOG_CACHE_PATH",
    "AGU_HISTORY_CACHE_DIR",
    "AGU_DATA_HEALTH_PATH",
    "AGU_DATASET_META_PATH",
    "AGU_PAPER_PORTFOLIO_PATH",
    "AGU_APP_PORT",
    "AGU_PORTFOLIO_DEFAULT_CASH",
]


class ConfigLoadTests(unittest.TestCase):
    def setUp(self) -> None:
        self._original_env = {key: os.environ.get(key) for key in CONFIG_ENV_KEYS}
        for key in CONFIG_ENV_KEYS:
            os.environ.pop(key, None)

    def tearDown(self) -> None:
        for key in CONFIG_ENV_KEYS:
            value = self._original_env.get(key)
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def test_default_paths_remain_stable_without_env(self) -> None:
        config = importlib.reload(importlib.import_module("app.core.config"))

        self.assertEqual(config.APP_PORT, 8000)
        self.assertEqual(config.PORTFOLIO_DEFAULT_CASH, 1_000_000.0)
        self.assertEqual(config.DATA_DIR, config.BASE_DIR / "data")
        self.assertEqual(config.MODELS_DIR, config.BASE_DIR / "models")
        self.assertEqual(config.DEFAULT_MODEL_PATH, config.MODELS_DIR / "stock_ranker.pkl")

    def test_env_overrides_support_relative_and_absolute_paths(self) -> None:
        base_dir = Path(self._temp_dir()) / "agu-base"
        os.environ["AGU_BASE_DIR"] = str(base_dir)
        os.environ["AGU_DATA_DIR"] = "custom-data"
        os.environ["AGU_MODELS_DIR"] = str(base_dir / "artifacts" / "models")
        os.environ["AGU_DEFAULT_MODEL_PATH"] = "trained/model.pkl"
        os.environ["AGU_APP_PORT"] = "8123"
        os.environ["AGU_PORTFOLIO_DEFAULT_CASH"] = "250000.5"

        config = importlib.reload(importlib.import_module("app.core.config"))

        self.assertEqual(config.BASE_DIR, base_dir.resolve())
        self.assertEqual(config.DATA_DIR, (base_dir / "custom-data").resolve())
        self.assertEqual(config.MODELS_DIR, (base_dir / "artifacts" / "models").resolve())
        self.assertEqual(config.DEFAULT_MODEL_PATH, (config.MODELS_DIR / "trained" / "model.pkl").resolve())
        self.assertEqual(config.APP_PORT, 8123)
        self.assertEqual(config.PORTFOLIO_DEFAULT_CASH, 250000.5)

    def _temp_dir(self) -> str:
        import tempfile

        return tempfile.gettempdir()


if __name__ == "__main__":
    unittest.main()
