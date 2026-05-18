"""Ranked Probability Score — the standard football metric for 1X2 forecasts.

Definition (Constantinou & Fenton 2012):
    RPS = (1 / (K-1)) * sum_{k=1..K-1} (sum_{j<=k} p_j - sum_{j<=k} o_j)^2

For 1X2 (K=3): outcomes are [home_win, draw, away_win].
Lower is better. Perfect = 0. Random uniform ≈ 0.25. Bookmaker closing ≈ 0.20-0.21.
"""

from __future__ import annotations

import numpy as np


def rps(probs: np.ndarray, outcomes: np.ndarray) -> np.ndarray:
    """Per-match RPS.

    Args:
        probs: (n, K) predicted probabilities, rows sum to 1.
        outcomes: (n,) int in [0, K). For 1X2: 0=home win, 1=draw, 2=away win.

    Returns:
        (n,) array of per-match RPS values.
    """
    probs = np.asarray(probs, dtype=float)
    outcomes = np.asarray(outcomes, dtype=int)
    n, k = probs.shape
    one_hot = np.zeros_like(probs)
    one_hot[np.arange(n), outcomes] = 1.0
    cum_p = np.cumsum(probs, axis=1)
    cum_o = np.cumsum(one_hot, axis=1)
    sq = (cum_p[:, :-1] - cum_o[:, :-1]) ** 2
    return sq.sum(axis=1) / (k - 1)


def mean_rps(probs: np.ndarray, outcomes: np.ndarray) -> float:
    return float(rps(probs, outcomes).mean())


def log_loss_1x2(probs: np.ndarray, outcomes: np.ndarray, eps: float = 1e-15) -> float:
    probs = np.clip(np.asarray(probs, dtype=float), eps, 1 - eps)
    outcomes = np.asarray(outcomes, dtype=int)
    return float(-np.log(probs[np.arange(len(outcomes)), outcomes]).mean())


def outcome_1x2(home_goals: int, away_goals: int) -> int:
    if home_goals > away_goals:
        return 0
    if home_goals == away_goals:
        return 1
    return 2
