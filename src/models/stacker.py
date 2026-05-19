"""Meta-learner that blends Dixon-Coles, LightGBM, and Bayesian 1X2 probabilities.

Strategy:
  1. For each base model, compute out-of-fold 1X2 probabilities on a calibration window.
  2. Fit a multinomial logistic regression on those probs (concat) -> blended 1X2.
  3. Re-calibrate with isotonic per class.

For convenience the stacker also exposes `predict_score_matrix(home, away)` that defaults
to using Dixon-Coles' score matrix re-weighted so its marginal 1X2 matches the blended
probabilities — preserves the joint distribution for Monte Carlo while honoring the
better-calibrated marginals.
"""

from __future__ import annotations

import pickle
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression


@dataclass
class Stacker:
    base_names: list[str]
    meta: LogisticRegression
    calibrators: list[IsotonicRegression]

    def predict_proba(self, base_probs: dict[str, np.ndarray]) -> np.ndarray:
        """base_probs: {name: (n,3) array}. Returns (n,3) blended + calibrated."""
        X = np.concatenate([base_probs[n] for n in self.base_names], axis=1)
        blended = self.meta.predict_proba(X)
        cal = np.column_stack([self.calibrators[k].predict(blended[:, k]) for k in range(3)])
        cal = np.clip(cal, 1e-6, 1 - 1e-6)
        cal /= cal.sum(axis=1, keepdims=True)
        return cal


def fit(base_probs_train: dict[str, np.ndarray], y_train: np.ndarray,
        base_probs_cal: dict[str, np.ndarray], y_cal: np.ndarray) -> Stacker:
    names = list(base_probs_train.keys())
    X_tr = np.concatenate([base_probs_train[n] for n in names], axis=1)
    X_cal = np.concatenate([base_probs_cal[n] for n in names], axis=1)
    meta = LogisticRegression(C=1.0, max_iter=2000, multi_class="multinomial")
    meta.fit(X_tr, y_tr)
    blended = meta.predict_proba(X_cal)
    cals = []
    for k in range(3):
        ir = IsotonicRegression(out_of_bounds="clip", y_min=1e-6, y_max=1 - 1e-6)
        ir.fit(blended[:, k], (y_cal == k).astype(float))
        cals.append(ir)
    return Stacker(base_names=names, meta=meta, calibrators=cals)


def reweight_score_matrix(score_matrix: np.ndarray, target_1x2: np.ndarray) -> np.ndarray:
    """Rescale a base score matrix so its marginal P(home win)/P(draw)/P(away win) matches `target_1x2`.

    target_1x2: array [p_home, p_draw, p_away] summing to 1.
    Preserves the relative shape *within* each 1X2 cell.
    """
    n = score_matrix.shape[0]
    mask_home = np.tril(np.ones((n, n)), k=-1)
    mask_draw = np.eye(n)
    mask_away = np.triu(np.ones((n, n)), k=1)
    cur = np.array(
        [(score_matrix * mask_home).sum(), (score_matrix * mask_draw).sum(), (score_matrix * mask_away).sum()]
    )
    cur = np.clip(cur, 1e-9, 1.0)
    scale = target_1x2 / cur
    out = score_matrix * (mask_home * scale[0] + mask_draw * scale[1] + mask_away * scale[2])
    return out / out.sum()


def save(stacker: Stacker, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump(stacker, f)


def load(path: str | Path) -> Stacker:
    with open(path, "rb") as f:
        return pickle.load(f)
