"""Dixon-Coles tau-adjusted joint score distribution, reconstructable from 1X2.

The Monte Carlo sim persists trusted blended 1X2 probabilities per match, but its
expected-goal columns can be polluted (pre-canonicalization runs fell back to a uniform
score matrix for unmatched team names, inflating goal expectations to ~5 per side).
The strategy layer needs a coherent joint P(home=i, away=j) for totals / exact-score
picks, so instead of trusting those goal columns we *invert* the 1X2 triple through an
independent-Poisson-with-DC-tau model: solve for the (home_rate, away_rate) pair whose
tau-adjusted joint reproduces the 1X2 exactly, then use that joint downstream.

The draw probability pins the total-goals scale and the win-probability ratio pins the
rate difference, so the inversion is well-identified with two free parameters.

`DEFAULT_RHO = -0.0565` is the fitted low-score correlation from the most recent full
Dixon-Coles fit in the repo (`data/models/cache/dc_2024-06-20.pkl`, last param).
"""

from __future__ import annotations

import math

import numpy as np

DEFAULT_RHO = -0.0565
_LOG_RATE_BOUNDS = (math.log(0.02), math.log(8.0))


def dc_tau_score_matrix(
    home_rate: float,
    away_rate: float,
    rho: float = DEFAULT_RHO,
    max_goals: int = 10,
) -> np.ndarray:
    """Joint P(home=i, away=j) = tau(i, j) * Pois(i; λh) * Pois(j; λa), renormalized.

    tau is the Dixon-Coles low-score adjustment: with rho < 0 it boosts 0-0 and 1-1
    and shaves 1-0 / 0-1, which is what independent Poisson gets wrong about draws.
    """
    n = max_goals + 1
    goals = np.arange(n)
    log_fact = np.cumsum(np.concatenate([[0.0], np.log(np.arange(1, n))])) if n > 1 else [0.0]
    ph = np.exp(goals * math.log(max(home_rate, 1e-12)) - home_rate - log_fact)
    pa = np.exp(goals * math.log(max(away_rate, 1e-12)) - away_rate - log_fact)
    sm = np.outer(ph, pa)
    tau = np.ones((n, n))
    tau[0, 0] = 1.0 - home_rate * away_rate * rho
    tau[0, 1] = 1.0 + home_rate * rho
    tau[1, 0] = 1.0 + away_rate * rho
    tau[1, 1] = 1.0 - rho
    sm = sm * np.clip(tau, 1e-9, None)
    return sm / sm.sum()


def one_x_two(score_matrix: np.ndarray) -> np.ndarray:
    """Marginal [P(home win), P(draw), P(away win)] of a joint score matrix."""
    n = score_matrix.shape[0]
    home = float((score_matrix * np.tril(np.ones((n, n)), k=-1)).sum())
    draw = float(np.trace(score_matrix))
    away = float((score_matrix * np.triu(np.ones((n, n)), k=1)).sum())
    return np.array([home, draw, away])


def _residual(z: np.ndarray, target: np.ndarray, rho: float, max_goals: int) -> np.ndarray:
    sm = dc_tau_score_matrix(math.exp(z[0]), math.exp(z[1]), rho=rho, max_goals=max_goals)
    p = one_x_two(sm)
    return np.array([p[0] - target[0], p[1] - target[1]])


def implied_rates_from_1x2(
    p_home: float,
    p_draw: float,
    p_away: float,
    rho: float = DEFAULT_RHO,
    max_goals: int = 10,
    init: tuple[float, float] | None = None,
) -> tuple[float, float]:
    """Solve for (home_rate, away_rate) whose DC-tau joint matches the 1X2 triple.

    Damped Newton on (log λh, log λa) with a numerical Jacobian; falls back to a coarse
    grid restart if the first basin doesn't converge. Raises ValueError on failure.
    """
    s = p_home + p_draw + p_away
    if s <= 0:
        raise ValueError("1X2 probabilities must have positive mass")
    target = np.array([p_home / s, p_draw / s])

    def solve_from(z0: np.ndarray) -> tuple[np.ndarray, float]:
        z = z0.copy()
        for _ in range(80):
            f = _residual(z, target, rho, max_goals)
            err = float(np.abs(f).max())
            if err < 1e-10:
                return z, err
            jac = np.empty((2, 2))
            eps = 1e-6
            for j in range(2):
                zp = z.copy()
                zp[j] += eps
                jac[:, j] = (_residual(zp, target, rho, max_goals) - f) / eps
            try:
                step = np.linalg.solve(jac, f)
            except np.linalg.LinAlgError:
                break
            norm = float(np.abs(step).max())
            if norm > 1.0:
                step *= 1.0 / norm
            z = np.clip(z - step, *_LOG_RATE_BOUNDS)
        return z, float(np.abs(_residual(z, target, rho, max_goals)).max())

    starts = [np.log(np.clip(np.array(init, dtype=float), 0.05, 8.0))] if init else []
    starts += [np.log([1.4, 1.1]), np.log([0.8, 0.8]), np.log([2.2, 1.0]), np.log([1.0, 2.2])]
    best_z, best_err = None, np.inf
    for z0 in starts:
        z, err = solve_from(z0)
        if err < best_err:
            best_z, best_err = z, err
        if best_err < 1e-9:
            break
    if best_z is None or best_err > 1e-6:
        raise ValueError(
            f"implied-rate inversion failed for 1X2=({p_home:.4f},{p_draw:.4f},{p_away:.4f}): "
            f"residual {best_err:.2e}"
        )
    return float(math.exp(best_z[0])), float(math.exp(best_z[1]))


def score_matrix_from_1x2(
    p_home: float,
    p_draw: float,
    p_away: float,
    rho: float = DEFAULT_RHO,
    max_goals: int = 10,
    init: tuple[float, float] | None = None,
) -> np.ndarray:
    """Coherent DC-tau joint whose 1X2 marginals equal the given triple."""
    lh, la = implied_rates_from_1x2(p_home, p_draw, p_away, rho=rho, max_goals=max_goals, init=init)
    return dc_tau_score_matrix(lh, la, rho=rho, max_goals=max_goals)
