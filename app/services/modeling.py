from __future__ import annotations

from pathlib import Path
import pickle
from typing import Any

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

from app.services.dataset import FEATURE_COLUMNS


FEATURE_LABELS = {
    "ret_5": "近5日收益",
    "ret_10": "近10日收益",
    "ret_20": "近20日收益",
    "volatility_10": "10日波动率",
    "volatility_20": "20日波动率",
    "price_vs_ma10": "相对10日均线",
    "price_vs_ma20": "相对20日均线",
    "ma_gap_10_20": "10/20日均线间距",
    "volume_ratio_5": "量比(5日)",
    "volume_ratio_20": "量比(20日)",
    "drawdown_20": "20日回撤",
    "momentum_spread_5_20": "短中期动量差",
}


def _format_percent_value(value: float | None, digits: int = 2, with_sign: bool = True) -> str:
    if value is None or pd.isna(value):
        return "-"
    numeric = float(value) * 100
    prefix = "+" if with_sign and numeric > 0 else ""
    return f"{prefix}{numeric:.{digits}f}%"


def _format_contribution_value(value: float | None, digits: int = 2) -> str:
    if value is None or pd.isna(value):
        return "-"
    numeric = float(value) * 100
    prefix = "+" if numeric > 0 else ""
    return f"{prefix}{numeric:.{digits}f}个百分点"


def _format_feature_value(feature: str, value: float | None) -> str:
    if value is None or pd.isna(value):
        return "-"
    numeric = float(value)
    if feature.startswith("ret_") or feature.startswith("price_vs_") or feature in {"ma_gap_10_20", "drawdown_20", "momentum_spread_5_20"}:
        return _format_percent_value(numeric)
    if feature.startswith("volatility_"):
        return _format_percent_value(numeric, with_sign=False)
    if feature.startswith("volume_ratio_"):
        return f"{numeric:.2f}倍"
    return f"{numeric:.4f}"


def _reason_tag(feature: str, value: float, contribution: float) -> str:
    if feature in {"ret_5", "ret_10", "ret_20", "momentum_spread_5_20"}:
        if contribution >= 0 and value >= 0:
            return "趋势动量偏强"
        if contribution >= 0:
            return "修复弹性占优"
        return "动量仍需验证"
    if feature in {"price_vs_ma10", "price_vs_ma20", "ma_gap_10_20"}:
        if contribution >= 0:
            return "均线结构占优"
        return "均线支撑偏弱"
    if feature in {"volume_ratio_5", "volume_ratio_20"}:
        if contribution >= 0:
            return "量能配合较好"
        return "量能配合一般"
    if feature in {"volatility_10", "volatility_20", "drawdown_20"}:
        if contribution >= 0:
            return "波动与回撤可控"
        return "波动回撤偏大"
    return FEATURE_LABELS.get(feature, feature)


def _positive_reason_text(feature: str, value: float, contribution: float) -> str:
    label = FEATURE_LABELS.get(feature, feature)
    value_display = _format_feature_value(feature, value)
    contribution_display = _format_contribution_value(contribution)
    if feature == "drawdown_20":
        return f"{label}为 {value_display}，近期回撤控制较好，对模型打分贡献 {contribution_display}。"
    return f"{label}为 {value_display}，当前形态对模型判断偏正面，贡献 {contribution_display}。"


def _risk_reason_text(feature: str, value: float, contribution: float) -> str:
    label = FEATURE_LABELS.get(feature, feature)
    value_display = _format_feature_value(feature, value)
    contribution_display = _format_contribution_value(contribution)
    if feature == "drawdown_20":
        return f"{label}为 {value_display}，说明近20日仍有回撤压力，拖累约 {contribution_display}。"
    return f"{label}为 {value_display}，当前对模型判断形成拖累，影响约 {contribution_display}。"


def _basis_text(feature: str, value: float, contribution: float) -> str:
    return f"{FEATURE_LABELS.get(feature, feature)} { _format_feature_value(feature, value) }，贡献 { _format_contribution_value(contribution) }"


def build_pick_explanations(model: LGBMRegressor, ranked_df: pd.DataFrame) -> pd.DataFrame:
    explained = ranked_df.copy().reset_index(drop=True)
    if explained.empty:
        explained["reason_summary"] = []
        explained["reason_tags"] = []
        explained["reason_texts"] = []
        explained["basis_items"] = []
        explained["risk_texts"] = []
        return explained

    contributions = model.predict(explained[FEATURE_COLUMNS], pred_contrib=True)
    contribution_array = np.asarray(contributions)
    if contribution_array.ndim == 1:
        contribution_array = contribution_array.reshape(1, -1)
    feature_contributions = contribution_array[:, : len(FEATURE_COLUMNS)]

    reason_summaries: list[str] = []
    reason_tags_list: list[list[str]] = []
    reason_texts_list: list[list[str]] = []
    basis_items_list: list[list[dict[str, Any]]] = []
    risk_texts_list: list[list[str]] = []

    for row_index, (_, row) in enumerate(explained.iterrows()):
        feature_items: list[dict[str, Any]] = []
        for feature_index, feature in enumerate(FEATURE_COLUMNS):
            value = float(row[feature]) if pd.notna(row[feature]) else None
            contribution = float(feature_contributions[row_index, feature_index])
            feature_items.append(
                {
                    "feature": feature,
                    "label": FEATURE_LABELS.get(feature, feature),
                    "value": value,
                    "value_display": _format_feature_value(feature, value),
                    "contribution": contribution,
                    "contribution_display": _format_contribution_value(contribution),
                    "is_positive": contribution >= 0,
                    "abs_contribution": abs(contribution),
                }
            )

        positive_items = sorted([item for item in feature_items if item["contribution"] > 0], key=lambda item: item["contribution"], reverse=True)
        negative_items = sorted([item for item in feature_items if item["contribution"] < 0], key=lambda item: item["contribution"])
        if not positive_items:
            positive_items = sorted(feature_items, key=lambda item: item["abs_contribution"], reverse=True)[:3]

        top_positive_items = positive_items[:3]
        top_negative_items = negative_items[:2]
        reason_tags = list(dict.fromkeys(_reason_tag(item["feature"], item["value"], item["contribution"]) for item in top_positive_items)) or ["综合因子占优"]
        reason_texts = [_positive_reason_text(item["feature"], item["value"], item["contribution"]) for item in top_positive_items]
        risk_texts = [_risk_reason_text(item["feature"], item["value"], item["contribution"]) for item in top_negative_items]
        basis_items = [
            {
                "label": item["label"],
                "value_display": item["value_display"],
                "contribution_display": item["contribution_display"],
                "is_positive": item["contribution"] >= 0,
                "text": _basis_text(item["feature"], item["value"], item["contribution"]),
            }
            for item in sorted(feature_items, key=lambda item: item["abs_contribution"], reverse=True)[:5]
        ]

        reason_summaries.append("、".join(reason_tags[:3]))
        reason_tags_list.append(reason_tags)
        reason_texts_list.append(reason_texts)
        basis_items_list.append(basis_items)
        risk_texts_list.append(risk_texts)

    explained["reason_summary"] = reason_summaries
    explained["reason_tags"] = reason_tags_list
    explained["reason_texts"] = reason_texts_list
    explained["basis_items"] = basis_items_list
    explained["risk_texts"] = risk_texts_list
    return explained


def build_backtest_summary(test_df: pd.DataFrame, predictions: np.ndarray, top_n: int = 10) -> dict[str, Any]:
    if test_df.empty:
        return {
            "days": 0,
            "top_n": top_n,
            "top_avg_return_5": None,
            "universe_avg_return_5": None,
            "excess_return_5": None,
            "hit_rate": None,
        }

    evaluation = test_df[["date", "symbol", "future_return_5"]].copy()
    evaluation["predicted_return_5"] = predictions

    daily_rows: list[dict[str, Any]] = []
    for trade_date, group in evaluation.groupby("date"):
        ranked = group.sort_values("predicted_return_5", ascending=False)
        picked = ranked.head(min(top_n, len(ranked)))
        daily_rows.append(
            {
                "date": pd.Timestamp(trade_date).strftime("%Y-%m-%d"),
                "top_avg_return_5": float(picked["future_return_5"].mean()),
                "universe_avg_return_5": float(group["future_return_5"].mean()),
                "hit_rate": float((picked["future_return_5"] > 0).mean()),
                "pick_count": int(len(picked)),
            }
        )

    daily_frame = pd.DataFrame(daily_rows)
    top_avg_return = float(daily_frame["top_avg_return_5"].mean())
    universe_avg_return = float(daily_frame["universe_avg_return_5"].mean())
    return {
        "days": int(len(daily_frame)),
        "top_n": int(top_n),
        "top_avg_return_5": top_avg_return,
        "universe_avg_return_5": universe_avg_return,
        "excess_return_5": top_avg_return - universe_avg_return,
        "hit_rate": float(daily_frame["hit_rate"].mean()),
    }


def train_model(feature_df: pd.DataFrame, output_path: Path) -> dict[str, Any]:
    ordered = feature_df.sort_values("date").reset_index(drop=True)
    cutoff_index = int(len(ordered) * 0.8)
    train_df = ordered.iloc[:cutoff_index]
    test_df = ordered.iloc[cutoff_index:]

    model = LGBMRegressor(
        n_estimators=240,
        learning_rate=0.05,
        max_depth=5,
        num_leaves=31,
        min_child_samples=24,
        subsample=0.9,
        colsample_bytree=0.9,
        random_state=42,
    )
    model.fit(train_df[FEATURE_COLUMNS], train_df["future_return_5"])

    train_predictions = model.predict(train_df[FEATURE_COLUMNS])
    test_predictions = model.predict(test_df[FEATURE_COLUMNS]) if not test_df.empty else train_predictions

    train_score = float(model.score(train_df[FEATURE_COLUMNS], train_df["future_return_5"]))
    test_score = float(model.score(test_df[FEATURE_COLUMNS], test_df["future_return_5"])) if not test_df.empty else train_score
    test_mae = float(mean_absolute_error(test_df["future_return_5"], test_predictions)) if not test_df.empty else float(mean_absolute_error(train_df["future_return_5"], train_predictions))
    test_rmse = float(mean_squared_error(test_df["future_return_5"], test_predictions, squared=False)) if not test_df.empty else float(mean_squared_error(train_df["future_return_5"], train_predictions, squared=False))
    direction_accuracy = (
        float(((test_predictions > 0) == (test_df["future_return_5"].to_numpy() > 0)).mean())
        if not test_df.empty
        else float(((train_predictions > 0) == (train_df["future_return_5"].to_numpy() > 0)).mean())
    )
    backtest = build_backtest_summary(test_df if not test_df.empty else train_df, test_predictions if not test_df.empty else train_predictions, top_n=10)
    feature_importances = [
        {"feature": feature, "label": FEATURE_LABELS.get(feature, feature), "importance": float(importance)}
        for feature, importance in sorted(zip(FEATURE_COLUMNS, model.feature_importances_, strict=True), key=lambda item: item[1], reverse=True)
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("wb") as fh:
        pickle.dump(model, fh)

    return {
        "train_rows": int(len(train_df)),
        "test_rows": int(len(test_df)),
        "train_r2": train_score,
        "test_r2": test_score,
        "test_mae": test_mae,
        "test_rmse": test_rmse,
        "direction_accuracy": direction_accuracy,
        "backtest": backtest,
        "feature_importances": feature_importances,
    }


def load_model(model_path: Path) -> LGBMRegressor:
    with model_path.open("rb") as fh:
        return pickle.load(fh)


def score_snapshot(model: LGBMRegressor, snapshot_df: pd.DataFrame) -> pd.DataFrame:
    ranked = snapshot_df.copy()
    ranked["predicted_return_5"] = model.predict(ranked[FEATURE_COLUMNS])
    ranked["score"] = ranked["predicted_return_5"].rank(ascending=False, method="first")
    return ranked.sort_values("predicted_return_5", ascending=False).reset_index(drop=True)
