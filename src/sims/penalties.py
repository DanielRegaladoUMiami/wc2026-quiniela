"""Penalty shootout simulator.

Calibrated logistic on strength differential. Returns 0 if home wins, 1 if away wins.
Strength is any scalar (Elo, attack rating, etc.) — caller passes whatever the predictor uses.
"""

from __future__ import annotations

import numpy as np


def shootout_prob(home_strength: float, away_strength: float) -> float:
    """P(home wins shootout) from strength differential."""
    p = 0.5 + 0.02 * (home_strength - away_strength)
    return float(np.clip(p, 0.3, 0.7))


def simulate_shootout(
    home_strength: float,
    away_strength: float,
    rng: np.random.Generator,
) -> int:
    """0 if home wins, 1 if away wins."""
    return int(rng.random() >= shootout_prob(home_strength, away_strength))
