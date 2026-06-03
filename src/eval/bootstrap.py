"""Bootstrap 95% CIs for RPS (and other metrics) on a prediction log."""

from __future__ import annotations

from collections.abc import Callable

import numpy as np

from src.eval.rps import rps as per_match_rps


def bootstrap_ci(
    probs: np.ndarray,
    outcomes: np.ndarray,
    n_resamples: int = 1000,
    metric: Callable[[np.ndarray, np.ndarray], float] | None = None,
    alpha: float = 0.05,
    random_seed: int = 42,
) -> dict:
    """Bootstrap CI for `metric(probs, outcomes)` resampling matches with replacement.

    Default metric: mean RPS. Returns dict with point estimate, ci_lo, ci_hi, samples.
    """
    probs = np.asarray(probs)
    outcomes = np.asarray(outcomes)
    n = len(outcomes)
    if n == 0:
        return {"point": float("nan"), "ci_lo": float("nan"), "ci_hi": float("nan"), "n": 0}

    rng = np.random.default_rng(random_seed)

    if metric is None:
        # Optimised path for RPS: precompute per-match RPS, bootstrap the mean.
        per_match = per_match_rps(probs, outcomes)
        point = float(per_match.mean())
        idx = rng.integers(0, n, size=(n_resamples, n))
        means = per_match[idx].mean(axis=1)
    else:
        point = float(metric(probs, outcomes))
        means = np.empty(n_resamples)
        for b in range(n_resamples):
            ix = rng.integers(0, n, size=n)
            means[b] = float(metric(probs[ix], outcomes[ix]))

    lo = float(np.quantile(means, alpha / 2))
    hi = float(np.quantile(means, 1 - alpha / 2))
    return {"point": point, "ci_lo": lo, "ci_hi": hi, "n": n, "n_resamples": n_resamples}
