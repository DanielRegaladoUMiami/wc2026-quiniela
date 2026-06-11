"""Tests for src.models.dc_joint — DC-tau joint + 1X2 inversion."""

from __future__ import annotations

import numpy as np
import pytest

from src.models.dc_joint import (
    dc_tau_score_matrix,
    implied_rates_from_1x2,
    one_x_two,
    score_matrix_from_1x2,
)


def _independent_poisson(lh: float, la: float, max_goals: int = 10) -> np.ndarray:
    return dc_tau_score_matrix(lh, la, rho=0.0, max_goals=max_goals)


def test_tau_matrix_normalized_and_nonnegative():
    sm = dc_tau_score_matrix(1.6, 0.9, rho=-0.06)
    assert sm.sum() == pytest.approx(1.0)
    assert (sm >= 0).all()


def test_negative_rho_boosts_low_draws():
    indep = _independent_poisson(1.4, 1.2)
    dc = dc_tau_score_matrix(1.4, 1.2, rho=-0.06)
    # DC with rho<0 boosts 0-0 and 1-1 and shaves 1-0 / 0-1.
    assert dc[0, 0] > indep[0, 0]
    assert dc[1, 1] > indep[1, 1]
    assert dc[1, 0] < indep[1, 0]
    assert dc[0, 1] < indep[0, 1]
    assert one_x_two(dc)[1] > one_x_two(indep)[1]


def test_one_x_two_sums_to_one():
    p = one_x_two(dc_tau_score_matrix(2.1, 0.7))
    assert p.sum() == pytest.approx(1.0)
    assert p[0] > p[2]  # higher home rate → home favored


@pytest.mark.parametrize(
    ("lh", "la"),
    [(1.6, 0.9), (0.8, 0.8), (2.5, 1.4), (0.5, 1.8), (1.1, 1.1)],
)
def test_inversion_round_trip(lh, la):
    rho = -0.0565
    target = one_x_two(dc_tau_score_matrix(lh, la, rho=rho))
    got_lh, got_la = implied_rates_from_1x2(*target, rho=rho)
    assert got_lh == pytest.approx(lh, abs=1e-4)
    assert got_la == pytest.approx(la, abs=1e-4)


def test_score_matrix_from_1x2_matches_target():
    # An arbitrary (not Poisson-generated) but plausible 1X2 triple.
    target = (0.55, 0.24, 0.21)
    sm = score_matrix_from_1x2(*target)
    got = one_x_two(sm)
    assert got == pytest.approx(np.array(target), abs=1e-7)


def test_unnormalized_input_is_normalized():
    sm = score_matrix_from_1x2(0.50, 0.30, 0.25)  # sums to 1.05
    got = one_x_two(sm)
    assert got == pytest.approx(np.array([0.50, 0.30, 0.25]) / 1.05, abs=1e-7)


def test_degenerate_input_raises():
    with pytest.raises(ValueError):
        implied_rates_from_1x2(0.0, 0.0, 0.0)
