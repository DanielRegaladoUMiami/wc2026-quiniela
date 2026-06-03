"""LightGBM 1X2 classifier on engineered features.

Inputs: data/processed/features_match_level.parquet (built by src.features.build_table).
Trains a multiclass classifier on (home_win=0, draw=1, away_win=2) using time-series CV
to prevent look-ahead, with isotonic calibration on a held-out window.

Outputs:
  data/models/lgbm_1x2.txt           — LightGBM booster
  data/models/lgbm_calibrators.pkl    — per-class isotonic regressors
"""

from __future__ import annotations

import pickle
from dataclasses import dataclass
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
import polars as pl
from sklearn.isotonic import IsotonicRegression

from src.eval.rps import log_loss_1x2, mean_rps

FEATURE_COLS = [
    "elo_diff",
    "home_elo_pre",
    "away_elo_pre",
    "p_home_win_elo",
    "importance",
    "h_ppg_5",
    "h_ppg_10",
    "h_ppg_20",
    "a_ppg_5",
    "a_ppg_10",
    "a_ppg_20",
    "h_gd_pm_5",
    "h_gd_pm_10",
    "h_gd_pm_20",
    "a_gd_pm_5",
    "a_gd_pm_10",
    "a_gd_pm_20",
    "h_gf_pm_10",
    "a_gf_pm_10",
    "h_ga_pm_10",
    "a_ga_pm_10",
    "h_win_rate_10",
    "a_win_rate_10",
    "h_ppg_vs_top_10",
    "a_ppg_vs_top_10",
    "h_gd_pm_vs_top_10",
    "a_gd_pm_vs_top_10",
    "h_days_since_last",
    "a_days_since_last",
    "form_diff_ppg_5",
    "form_diff_ppg_10",
    "form_diff_ppg_20",
    "form_diff_gd_5",
    "form_diff_gd_10",
    "form_diff_gd_20",
]

DEFAULT_PARAMS = {
    "objective": "multiclass",
    "num_class": 3,
    "metric": "multi_logloss",
    "learning_rate": 0.05,
    "num_leaves": 63,
    "min_data_in_leaf": 50,
    "feature_fraction": 0.85,
    "bagging_fraction": 0.85,
    "bagging_freq": 5,
    "lambda_l2": 1.0,
    "verbose": -1,
}


@dataclass
class GBMModel:
    booster: lgb.Booster
    calibrators: list[IsotonicRegression]
    feature_cols: list[str]

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        raw = self.booster.predict(
            X[self.feature_cols].to_numpy(), num_iteration=self.booster.best_iteration
        )
        if raw.ndim == 1:
            raw = raw.reshape(-1, 3)
        cal = np.column_stack([self.calibrators[k].predict(raw[:, k]) for k in range(3)])
        cal = np.clip(cal, 1e-6, 1 - 1e-6)
        cal /= cal.sum(axis=1, keepdims=True)
        return cal


def _prepare(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["date"] = pd.to_datetime(out["date"])
    out = out.dropna(subset=["outcome"]).copy()
    for c in FEATURE_COLS:
        if c not in out.columns:
            out[c] = np.nan
    out = out.dropna(subset=["home_elo_pre", "away_elo_pre"])
    return out


def fit(
    matches: pd.DataFrame,
    train_end: pd.Timestamp,
    valid_end: pd.Timestamp,
    params: dict | None = None,
    num_boost_round: int = 2000,
    early_stopping_rounds: int = 80,
) -> GBMModel:
    df = _prepare(matches)
    params = {**DEFAULT_PARAMS, **(params or {})}

    train_end = pd.Timestamp(train_end)
    valid_end = pd.Timestamp(valid_end)
    train = df[df["date"] < train_end]
    valid = df[(df["date"] >= train_end) & (df["date"] < valid_end)]
    print(f"Train: {len(train):,}  Valid: {len(valid):,}")

    X_tr, y_tr = train[FEATURE_COLS].to_numpy(), train["outcome"].astype(int).to_numpy()
    X_va, y_va = valid[FEATURE_COLS].to_numpy(), valid["outcome"].astype(int).to_numpy()
    dtr = lgb.Dataset(X_tr, label=y_tr)
    dva = lgb.Dataset(X_va, label=y_va, reference=dtr)

    booster = lgb.train(
        params,
        dtr,
        num_boost_round=num_boost_round,
        valid_sets=[dtr, dva],
        valid_names=["train", "valid"],
        callbacks=[
            lgb.early_stopping(early_stopping_rounds, verbose=False),
            lgb.log_evaluation(period=100),
        ],
    )

    raw_va = booster.predict(X_va, num_iteration=booster.best_iteration).reshape(-1, 3)
    calibrators: list[IsotonicRegression] = []
    for k in range(3):
        ir = IsotonicRegression(out_of_bounds="clip", y_min=1e-6, y_max=1 - 1e-6)
        ir.fit(raw_va[:, k], (y_va == k).astype(float))
        calibrators.append(ir)

    model = GBMModel(booster=booster, calibrators=calibrators, feature_cols=FEATURE_COLS)
    cal_probs = model.predict_proba(valid)
    print(f"Validation log-loss: {log_loss_1x2(cal_probs, y_va):.4f}")
    print(f"Validation RPS:      {mean_rps(cal_probs, y_va):.4f}")
    return model


def save(model: GBMModel, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    model.booster.save_model(str(path))
    with open(path.with_suffix(".calibrators.pkl"), "wb") as f:
        pickle.dump({"calibrators": model.calibrators, "feature_cols": model.feature_cols}, f)


def load(path: str | Path) -> GBMModel:
    path = Path(path)
    booster = lgb.Booster(model_file=str(path))
    with open(path.with_suffix(".calibrators.pkl"), "rb") as f:
        meta = pickle.load(f)
    return GBMModel(
        booster=booster, calibrators=meta["calibrators"], feature_cols=meta["feature_cols"]
    )


def main() -> int:
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--features", default="data/processed/features_match_level.parquet")
    p.add_argument("--train-end", default="2022-01-01")
    p.add_argument("--valid-end", default="2024-06-01")
    p.add_argument("--out", default="data/models/lgbm_1x2.txt")
    args = p.parse_args()

    df = pl.read_parquet(args.features).to_pandas()
    print(f"Loaded {len(df):,} matches with features")
    model = fit(df, train_end=args.train_end, valid_end=args.valid_end)
    save(model, args.out)
    print(f"Saved → {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
