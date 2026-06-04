"""Tests for de-vigging bookmaker 1X2 odds into honest probabilities."""

from __future__ import annotations

import math

import pytest

from src.data.devig import (
    american_to_decimal,
    proportional_devig,
    shin_devig,
    vig_pct,
)


def test_american_to_decimal():
    assert american_to_decimal(-225) == pytest.approx(1 + 100 / 225)
    assert american_to_decimal(+700) == pytest.approx(8.0)
    assert american_to_decimal("+100") == pytest.approx(2.0)
    assert american_to_decimal("EVEN") == pytest.approx(2.0)
    assert american_to_decimal("-110") == pytest.approx(1 + 100 / 110)


@pytest.mark.parametrize("devig", [proportional_devig, shin_devig])
def test_devig_sums_to_one(devig):
    # DraftKings WC2026 opener: MEX -225 / draw +340 / RSA +700
    o = (american_to_decimal(-225), american_to_decimal(340), american_to_decimal(700))
    p_h, p_d, p_a = devig(*o)
    assert math.isclose(p_h + p_d + p_a, 1.0, abs_tol=1e-9)
    assert all(0.0 < p < 1.0 for p in (p_h, p_d, p_a))


@pytest.mark.parametrize("devig", [proportional_devig, shin_devig])
def test_favorite_stays_favorite(devig):
    # Shortest price (home) must map to the largest probability, longest to smallest.
    o_h, o_d, o_a = 1.44, 4.4, 8.0
    p_h, p_d, p_a = devig(o_h, o_d, o_a)
    assert p_h > p_d > p_a


def test_devig_removes_the_vig():
    # A book with ~6% overround must produce probabilities that sum to exactly 1
    # (i.e. strictly less mass than the raw 1/odds, which sum to > 1).
    o_h, o_d, o_a = 1.44, 4.4, 8.0
    raw = 1 / o_h + 1 / o_d + 1 / o_a
    assert raw > 1.0  # there is vig to remove
    p = shin_devig(o_h, o_d, o_a)
    assert math.isclose(sum(p), 1.0, abs_tol=1e-9)
    assert vig_pct(o_h, o_d, o_a) > 0


def test_no_vig_is_identity():
    # Fair odds whose 1/odds already sum to 1 should pass through unchanged.
    o_h, o_d, o_a = 2.0, 4.0, 4.0  # 0.5 + 0.25 + 0.25 = 1.0
    p_h, p_d, p_a = shin_devig(o_h, o_d, o_a)
    assert (p_h, p_d, p_a) == pytest.approx((0.5, 0.25, 0.25))


def test_shin_pulls_less_from_favorite_than_proportional():
    # Shin's correction leaves the favorite with slightly MORE probability than
    # naive proportional de-vig (it attributes part of the overround to insiders).
    o_h, o_d, o_a = 1.30, 5.5, 11.0
    sh = shin_devig(o_h, o_d, o_a)
    pr = proportional_devig(o_h, o_d, o_a)
    assert sh[0] >= pr[0] - 1e-9
