"""Fit the meta-learner stacker on OOF predictions from generate_oof.

Strategy:
  1. Load OOF parquet with cols p_dc_{h,d,a}, p_gbm_{h,d,a}, p_bay_{h,d,a}, outcome.
  2. Build feature matrix X = concat of 9 columns; y = outcome.
  3. Time-based split: train on older tournaments, validate on newer.
  4. Fit `LogisticRegression(multi_class='multinomial')` with C=1.0.
  5. Calibrate output per class with sigmoid (Platt) on the validation fold —
     isotonic needs more OOF rows than we have.
  6. Save the trained Stacker via `src.models.stacker.save`.

The SHIPPED artifact is exactly the configuration evaluated on validation:
train-fold meta + val-fold Platt calibrators. The meta deliberately does NOT
refit on all OOF rows — that would leave no held-out fold to calibrate on
without leakage, which is how the old IdentityCalibrator bug happened.

Reports RPS / log-loss on:
  - simple average baseline
  - logistic blend (no calibration)
  - logistic blend + sigmoid (= the shipped stacker)
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import polars as pl
from sklearn.linear_model import LogisticRegression

from src.eval.rps import log_loss_1x2, mean_rps
from src.models.stacker import Stacker
from src.models.stacker import save as save_stacker

BASE_COLS = [
    "p_dc_h",
    "p_dc_d",
    "p_dc_a",
    "p_gbm_h",
    "p_gbm_d",
    "p_gbm_a",
    "p_bay_h",
    "p_bay_d",
    "p_bay_a",
]


def _to_matrix(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, dict[str, np.ndarray]]:
    df = df.copy()
    df = df.dropna(subset=[*BASE_COLS, "outcome"])
    X = df[BASE_COLS].to_numpy(dtype=float)
    y = df["outcome"].astype(int).to_numpy()
    base = {
        "dc": df[["p_dc_h", "p_dc_d", "p_dc_a"]].to_numpy(),
        "gbm": df[["p_gbm_h", "p_gbm_d", "p_gbm_a"]].to_numpy(),
        "bay": df[["p_bay_h", "p_bay_d", "p_bay_a"]].to_numpy(),
    }
    return X, y, base


def _evaluate(name: str, probs: np.ndarray, y: np.ndarray) -> dict:
    res = {
        "name": name,
        "n": len(y),
        "rps": mean_rps(probs, y),
        "log_loss": log_loss_1x2(probs, y),
        "accuracy": float((probs.argmax(axis=1) == y).mean()),
    }
    print(
        f"  {name:30s}  RPS={res['rps']:.4f}  LL={res['log_loss']:.4f}  acc={res['accuracy']:.3f}"
    )
    return res


def main() -> int:
    df = pl.read_parquet("data/processed/oof_predictions.parquet").to_pandas()
    df["date"] = pd.to_datetime(df["date"])
    print(f"Loaded {len(df):,} OOF rows across {df['tournament'].nunique()} tournaments")

    train_keys = ["wc18", "wc22"]
    val_keys = ["euro24", "copa24"]
    train_df = df[df["tournament"].isin(train_keys)]
    val_df = df[df["tournament"].isin(val_keys)]
    print(f"Train: {len(train_df)} ({train_keys}). Val: {len(val_df)} ({val_keys}).")

    X_tr, y_tr, _base_tr = _to_matrix(train_df)
    X_va, y_va, base_va = _to_matrix(val_df)

    print("\n=== Validation metrics ===")
    for k, p in base_va.items():
        _evaluate(f"base {k}", p, y_va)

    avg_val = np.mean([base_va[k] for k in ("dc", "gbm", "bay")], axis=0)
    avg_val = avg_val / avg_val.sum(axis=1, keepdims=True)
    _evaluate("simple average (current)", avg_val, y_va)

    print("\n=== Fitting logistic stacker (train fold only) ===")
    lr = LogisticRegression(C=1.0, max_iter=2000)
    lr.fit(X_tr, y_tr)
    blended_va = lr.predict_proba(X_va)
    _evaluate("logistic stack (uncalibrated)", blended_va, y_va)

    print("\n=== Fitting sigmoid (Platt) calibration per class on val fold ===")
    sig_cals: list[LogisticRegression] = []
    for k in range(3):
        c = LogisticRegression(C=1.0, max_iter=2000)
        c.fit(blended_va[:, k].reshape(-1, 1), (y_va == k).astype(int))
        sig_cals.append(c)
    cal_va = np.column_stack(
        [sig_cals[k].predict_proba(blended_va[:, k].reshape(-1, 1))[:, 1] for k in range(3)]
    )
    cal_va = np.clip(cal_va, 1e-6, 1 - 1e-6)
    cal_va /= cal_va.sum(axis=1, keepdims=True)
    _evaluate("logistic stack + sigmoid", cal_va, y_va)

    print("\nLogReg weights (sign + magnitude per (input, output class)):")
    print(
        pd.DataFrame(lr.coef_, columns=BASE_COLS, index=["home_win", "draw", "away_win"]).round(2)
    )

    print("\n=== Shipping train-fold meta + val-fold Platt calibrators ===")
    stacker = Stacker(
        base_names=["dc", "gbm", "bay"],
        meta=lr,
        calibrators=sig_cals,
    )
    out = Path("data/models/stacker.pkl")
    save_stacker(stacker, out)
    print(f"\nSaved stacker → {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
