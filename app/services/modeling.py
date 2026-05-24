from __future__ import annotations

from pathlib import Path
import pickle

import pandas as pd
from lightgbm import LGBMRegressor

from app.services.dataset import FEATURE_COLUMNS


def train_model(feature_df: pd.DataFrame, output_path: Path) -> dict:
    ordered = feature_df.sort_values("date").reset_index(drop=True)
    cutoff_index = int(len(ordered) * 0.8)
    train_df = ordered.iloc[:cutoff_index]
    test_df = ordered.iloc[cutoff_index:]

    model = LGBMRegressor(
        n_estimators=200,
        learning_rate=0.05,
        max_depth=4,
        num_leaves=31,
        min_child_samples=20,
        subsample=0.9,
        colsample_bytree=0.9,
        random_state=42,
    )
    model.fit(train_df[FEATURE_COLUMNS], train_df["future_return_5"])

    train_score = float(model.score(train_df[FEATURE_COLUMNS], train_df["future_return_5"]))
    test_score = float(model.score(test_df[FEATURE_COLUMNS], test_df["future_return_5"])) if not test_df.empty else train_score

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("wb") as fh:
        pickle.dump(model, fh)

    return {
        "train_rows": int(len(train_df)),
        "test_rows": int(len(test_df)),
        "train_r2": train_score,
        "test_r2": test_score,
    }


def load_model(model_path: Path) -> LGBMRegressor:
    with model_path.open("rb") as fh:
        return pickle.load(fh)


def score_snapshot(model: LGBMRegressor, snapshot_df: pd.DataFrame) -> pd.DataFrame:
    ranked = snapshot_df.copy()
    ranked["predicted_return_5"] = model.predict(ranked[FEATURE_COLUMNS])
    ranked["score"] = ranked["predicted_return_5"].rank(ascending=False, method="first")
    ranked = ranked.sort_values("predicted_return_5", ascending=False).reset_index(drop=True)
    return ranked

