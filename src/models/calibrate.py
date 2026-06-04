"""Fit a single confidence-sharpening (temperature) parameter on the OOF backtest.

The base ensemble is systematically *flat* on mid-tier matchups — it sits near 1/3-1/3-1/3
when the sharp market is confident. We correct this with one scalar gamma applied as a power
transform  p_i^gamma / sum_j p_j^gamma  (gamma > 1 sharpens, < 1 flattens). gamma is fit on the
leakage-free out-of-fold predictions to minimize multiclass log-loss — one parameter over 211
matches, so it cannot overfit the way per-class isotonic did.

Output: data/models/temperature.json  ({"gamma": ...})
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar

OOF = Path("data/processed/oof_predictions.parquet")
OUT = Path("data/models/temperature.json")


def ensemble_probs(df: pd.DataFrame) -> np.ndarray:
    """Simple-mean ensemble of the three base models, row-normalized to sum 1."""
    h = df[["p_dc_h", "p_gbm_h", "p_bay_h"]].mean(axis=1)
    d = df[["p_dc_d", "p_gbm_d", "p_bay_d"]].mean(axis=1)
    a = df[["p_dc_a", "p_gbm_a", "p_bay_a"]].mean(axis=1)
    p = np.vstack([h, d, a]).T
    return p / p.sum(axis=1, keepdims=True)


def sharpen(p: np.ndarray, gamma: float) -> np.ndarray:
    """Temperature/power sharpening of a probability vector or matrix."""
    q = np.power(np.clip(p, 1e-12, 1.0), gamma)
    return q / q.sum(axis=-1, keepdims=True)


def _logloss(p: np.ndarray, y: np.ndarray) -> float:
    return float(-np.mean(np.log(np.clip(p[np.arange(len(y)), y], 1e-12, 1.0))))


def _rps(p: np.ndarray, y: np.ndarray) -> float:
    """Ranked Probability Score for ordinal 1X2 (home<draw<away)."""
    onehot = np.zeros_like(p)
    onehot[np.arange(len(y)), y] = 1.0
    cp, co = np.cumsum(p, axis=1), np.cumsum(onehot, axis=1)
    return float(np.mean(np.sum((cp - co) ** 2, axis=1) / (p.shape[1] - 1)))


def fit() -> dict:
    df = pd.read_parquet(OOF)
    y = df["outcome"].to_numpy().astype(int)
    base = ensemble_probs(df)

    res = minimize_scalar(
        lambda g: _logloss(sharpen(base, g), y), bounds=(0.5, 4.0), method="bounded"
    )
    gamma = float(res.x)

    out = {
        "gamma": gamma,
        "n": len(y),
        "logloss_before": _logloss(base, y),
        "logloss_after": _logloss(sharpen(base, gamma), y),
        "rps_before": _rps(base, y),
        "rps_after": _rps(sharpen(base, gamma), y),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2))
    return out


def load_gamma(default: float = 1.0) -> float:
    if OUT.exists():
        return float(json.loads(OUT.read_text())["gamma"])
    return default


def main() -> int:
    out = fit()
    print(f"Fitted temperature gamma = {out['gamma']:.3f} on {out['n']} OOF matches")
    print(f"  log-loss: {out['logloss_before']:.4f} -> {out['logloss_after']:.4f}")
    print(f"  RPS:      {out['rps_before']:.4f} -> {out['rps_after']:.4f}")
    print(f"  wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
