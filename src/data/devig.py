"""De-vigging: turn bookmaker 1X2 prices into honest (vig-free) probabilities.

A bookmaker's quoted odds imply probabilities that sum to > 1 — the excess is the
"vig" / "overround" (the house edge). To anchor a model to the market we need the
*true* implied probabilities, which sum to 1. Two methods are provided:

  - proportional: p_i = (1/o_i) / Σ(1/o_j). Simple; mildly overstates favorites.
  - shin: Shin (1992) — models a fraction `z` of insider money, which removes the
    favorite-longshot bias better. This is the default a sharp shop would use.

All odds here are DECIMAL (e.g. 2.50). Helpers convert American odds first.
"""

from __future__ import annotations

import numpy as np


def american_to_decimal(american: float | int | str) -> float:
    """Convert American moneyline odds (e.g. -225, +700, 'EVEN') to decimal odds."""
    if american is None:
        raise ValueError("american odds is None")
    if isinstance(american, str):
        s = american.strip().upper().replace("EVEN", "+100").replace("EV", "+100")
        a = float(s)
    else:
        a = float(american)
    if a == 0:
        raise ValueError("american odds cannot be 0")
    return 1.0 + (a / 100.0 if a > 0 else 100.0 / abs(a))


def proportional_devig(o_h: float, o_d: float, o_a: float) -> tuple[float, float, float]:
    """Basic normalization de-vig."""
    r = np.array([1.0 / o_h, 1.0 / o_d, 1.0 / o_a], dtype=float)
    p = r / r.sum()
    return float(p[0]), float(p[1]), float(p[2])


def shin_devig(o_h: float, o_d: float, o_a: float, iters: int = 80) -> tuple[float, float, float]:
    """Shin (1992) de-vig for a 1X2 market. Returns true probabilities summing to 1.

    Solves for the insider proportion z in [0, 0.5) such that the Shin-implied
    probabilities sum to 1, via bisection (the sum is monotone decreasing in z).
    """
    r = np.array([1.0 / o_h, 1.0 / o_d, 1.0 / o_a], dtype=float)
    phi = r.sum()  # overround; > 1 when there is vig
    if phi <= 1.0 + 1e-12:  # no vig (or arbitrage) — nothing to remove
        p = r / r.sum()
        return float(p[0]), float(p[1]), float(p[2])

    def p_of_z(z: float) -> np.ndarray:
        return (np.sqrt(z * z + 4.0 * (1.0 - z) * r * r / phi) - z) / (2.0 * (1.0 - z))

    lo, hi = 0.0, 0.5
    # If even z=0.5 leaves the sum > 1 (extreme vig), fall back to proportional.
    if p_of_z(hi).sum() > 1.0:
        return proportional_devig(o_h, o_d, o_a)
    for _ in range(iters):
        z = 0.5 * (lo + hi)
        if p_of_z(z).sum() > 1.0:
            lo = z
        else:
            hi = z
    p = p_of_z(0.5 * (lo + hi))
    p = p / p.sum()  # tiny renormalization for numerical safety
    return float(p[0]), float(p[1]), float(p[2])


def devig_1x2(
    o_h: float, o_d: float, o_a: float, method: str = "shin"
) -> tuple[float, float, float]:
    """De-vig decimal 1X2 odds with the chosen method ('shin' or 'proportional')."""
    if method == "proportional":
        return proportional_devig(o_h, o_d, o_a)
    if method == "shin":
        return shin_devig(o_h, o_d, o_a)
    raise ValueError(f"unknown devig method: {method}")


def vig_pct(o_h: float, o_d: float, o_a: float) -> float:
    """Overround (house margin) as a percentage, e.g. 5.2 for a 5.2% book."""
    return float((1.0 / o_h + 1.0 / o_d + 1.0 / o_a - 1.0) * 100.0)
