"""Tests for src.strategy.* — synthetic-data only, no live model required."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.strategy import (
    BracketPick,
    Entry,
    best_1x2_pick,
    best_exact_score_pick,
    best_fifa_mx_pick,
    estimate_public_champion,
    estimate_public_picks,
    expected_points,
    load_rubric,
    optimize_entries,
    pick_bracket,
)

CONFIGS = Path(__file__).resolve().parents[1] / "configs" / "rubrics"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def fifa_rubric():
    return load_rubric(CONFIGS / "fifa_quiniela_mx.yaml")


@pytest.fixture
def exact_rubric():
    return load_rubric(CONFIGS / "exact_score.yaml")


@pytest.fixture
def bracket_rubric():
    return load_rubric(CONFIGS / "espn_bracket.yaml")


def _score_matrix(entries: dict[tuple[int, int], float], max_g: int = 5) -> np.ndarray:
    m = np.zeros((max_g + 1, max_g + 1))
    for (i, j), p in entries.items():
        m[i, j] = p
    m = m / m.sum()
    return m


# ---------------------------------------------------------------------------
# Rubric loading
# ---------------------------------------------------------------------------


def test_load_all_rubrics(fifa_rubric, exact_rubric, bracket_rubric):
    assert fifa_rubric.name == "fifa_quiniela_mx"
    assert exact_rubric.name == "exact_score"
    assert bracket_rubric.name == "espn_bracket"


def test_fifa_rubric_scoring(fifa_rubric):
    # actual = 2-1 home win, total 3 goals (OVER 2.5)
    actual = (2, 1)
    assert fifa_rubric.score_function(("H", "OVER"), actual) == 5  # both right
    assert fifa_rubric.score_function(("H", "UNDER"), actual) == 3  # 1X2 only
    assert fifa_rubric.score_function(("D", "OVER"), actual) == 2  # totals only
    assert fifa_rubric.score_function(("A", "UNDER"), actual) == 0


def test_exact_rubric_tiers(exact_rubric):
    f = exact_rubric.score_function
    # actual 2-1
    assert f((2, 1), (2, 1)) == 5  # exact
    assert f((3, 2), (2, 1)) == 3  # GD=+1, winner H
    assert f((4, 0), (2, 1)) == 1  # winner only
    assert f((0, 1), (2, 1)) == 0  # wrong winner


# ---------------------------------------------------------------------------
# Expected-points argmax: hand-crafted exact-score scenario
# ---------------------------------------------------------------------------


def test_exact_score_argmax_known_optimum(exact_rubric):
    """
    P(0,0)=P(1,1)=P(2,1)=1/3.
    Picking (1,1):  P=1/3 → 5 (exact);
                    (0,0): wrong winner (both draws though) → GD=0 same → 3
                    (2,1): wrong winner (H vs D) → 0
                    E = 1/3*5 + 1/3*3 + 0 = 8/3 ≈ 2.667
    Picking (0,0):  exact 5 ; (1,1) GD same draw → 3 ; (2,1) wrong → 0
                    E = 8/3 ≈ 2.667
    Picking (2,1):  exact 5 ; (1,1) wrong winner → 0 ; (0,0) wrong winner → 0
                    E = 5/3 ≈ 1.667
    Best: (0,0) or (1,1) tied at 8/3.
    """
    sm = _score_matrix({(0, 0): 1 / 3, (1, 1): 1 / 3, (2, 1): 1 / 3})
    pick, ev = best_exact_score_pick(sm, exact_rubric)
    assert pick in {(0, 0), (1, 1)}
    assert ev == pytest.approx(8 / 3, abs=1e-6)


def test_exact_score_argmax_beats_mode(exact_rubric):
    """Mode is (3,0) with 0.30 but optimal pick is something more 'central'."""
    sm = _score_matrix(
        {
            (3, 0): 0.30,
            (1, 0): 0.25,
            (2, 0): 0.25,
            (2, 1): 0.20,
        }
    )
    _pick, ev = best_exact_score_pick(sm, exact_rubric)
    # picking the mode (3,0) gives:  0.30*5 + 0.25*1 + 0.25*3 + 0.20*1 = 2.7
    mode_ev = expected_points(
        (3, 0),
        {(3, 0): 0.30, (1, 0): 0.25, (2, 0): 0.25, (2, 1): 0.20},
        exact_rubric,
    )
    assert ev >= mode_ev  # argmax dominates mode


def test_best_1x2_pick(fifa_rubric):
    pick, ev = best_1x2_pick(0.6, 0.25, 0.15, fifa_rubric)
    assert pick == "H"
    # Under fifa-mx rubric with totals defaulted to UNDER and the (1,0)/(0,0)/(0,1)
    # representative outcomes, totals is always correct: 0.6*3 + 1.0*2 = 3.8
    assert ev == pytest.approx(3.8, abs=1e-6)


def test_best_fifa_mx_pick(fifa_rubric):
    sm = _score_matrix({(1, 0): 0.5, (2, 1): 0.3, (0, 0): 0.2})
    pick, ev = best_fifa_mx_pick(sm, fifa_rubric)
    assert pick[0] == "H"
    assert pick[1] in {"OVER", "UNDER"}
    assert ev > 0


# ---------------------------------------------------------------------------
# Public estimator
# ---------------------------------------------------------------------------


def _make_match_probs(n: int = 3) -> pd.DataFrame:
    rng = np.random.default_rng(0)
    rows = []
    for k in range(n):
        ph = rng.uniform(0.3, 0.6)
        pa = rng.uniform(0.2, 0.5)
        pd_ = max(1.0 - ph - pa, 0.05)
        s = ph + pa + pd_
        ph, pa, pd_ = ph / s, pa / s, pd_ / s
        sm = np.zeros((6, 6))
        sm[1, 0] = ph
        sm[0, 1] = pa
        sm[0, 0] = pd_
        sm = sm / sm.sum()
        rows.append(
            {
                "match_num": k + 1,
                "home_team": f"H{k}",
                "away_team": f"A{k}",
                "p_home_win": ph,
                "p_draw": pd_,
                "p_away_win": pa,
                "score_matrix": sm,
            }
        )
    return pd.DataFrame(rows)


def test_public_estimator_zero_square_matches_market():
    match = _make_match_probs(3)
    market = match[["match_num", "p_home_win", "p_draw", "p_away_win"]].copy()
    market["p_home_win"] = [0.4, 0.5, 0.6]
    market["p_draw"] = [0.3, 0.2, 0.2]
    market["p_away_win"] = [0.3, 0.3, 0.2]
    out = estimate_public_picks(match, market_probs=market, square_money_weight=0.0)
    assert out["public_p_home"].tolist() == pytest.approx([0.4, 0.5, 0.6])
    assert out["public_p_draw"].tolist() == pytest.approx([0.3, 0.2, 0.2])
    assert out["public_p_away"].tolist() == pytest.approx([0.3, 0.3, 0.2])


def test_public_estimator_full_square_collapses_to_favorite():
    match = _make_match_probs(2)
    out = estimate_public_picks(match, market_probs=None, square_money_weight=1.0)
    # Every favorite gets 1.0, draws get 0.
    for _, r in out.iterrows():
        assert r["public_p_draw"] == 0.0
        assert (r["public_p_home"] == 1.0) != (r["public_p_away"] == 1.0)


# ---------------------------------------------------------------------------
# optimize_entries
# ---------------------------------------------------------------------------


def test_optimize_entries_returns_n_distinct(fifa_rubric):
    match = _make_match_probs(5)
    public = estimate_public_picks(match, square_money_weight=0.7)
    entries = optimize_entries(match, public, fifa_rubric, n_entries=3, diversity_weight=0.5)
    assert len(entries) == 3
    assert all(isinstance(e, Entry) for e in entries)
    # at least one entry should diverge from chalk
    chalk_picks = entries[0].picks["pick"].tolist()
    other_picks = [e.picks["pick"].tolist() for e in entries[1:]]
    assert any(p != chalk_picks for p in other_picks)
    # chalk should have the highest expected points
    assert entries[0].expected_points >= max(e.expected_points for e in entries[1:])


def test_optimize_entries_exact_score(exact_rubric):
    match = _make_match_probs(3)
    public = estimate_public_picks(match, square_money_weight=0.5)
    entries = optimize_entries(match, public, exact_rubric, n_entries=2, diversity_weight=0.4)
    assert len(entries) == 2
    # Each pick must be a valid (i, j) tuple
    for e in entries:
        for p in e.picks["pick"]:
            assert isinstance(p, tuple) and len(p) == 2
            assert 0 <= p[0] <= 5 and 0 <= p[1] <= 5


# ---------------------------------------------------------------------------
# Bracket
# ---------------------------------------------------------------------------


def _make_advancement(n: int = 32) -> pd.DataFrame:
    rng = np.random.default_rng(1)
    teams = [f"T{i:02d}" for i in range(n)]
    p_adv = rng.uniform(0.3, 0.9, n)
    p_r16 = p_adv * rng.uniform(0.4, 0.95, n)
    p_qf = p_r16 * rng.uniform(0.3, 0.8, n)
    p_sf = p_qf * rng.uniform(0.2, 0.7, n)
    p_f = p_sf * rng.uniform(0.2, 0.6, n)
    p_champ = p_f * rng.uniform(0.2, 0.6, n)
    return pd.DataFrame(
        {
            "team": teams,
            "p_advance": p_adv,
            "p_R16": p_r16,
            "p_QF": p_qf,
            "p_SF": p_sf,
            "p_final": p_f,
            "p_champion": p_champ,
        }
    )


def test_pick_bracket_runs(bracket_rubric):
    adv = _make_advancement(32)
    out = pick_bracket(adv, bracket_rubric)
    assert isinstance(out, BracketPick)
    assert out.expected_points > 0
    assert "R32" in out.picks_by_round
    assert "W" in out.picks_by_round
    assert len(out.picks_by_round["W"]) == 1
    assert len(out.picks_by_round["R32"]) == 32


def test_pick_bracket_contrarian_changes_picks(bracket_rubric):
    adv = _make_advancement(32)
    public = estimate_public_champion(adv, square_money_weight=0.5)
    chalk = pick_bracket(adv, bracket_rubric)
    contra = pick_bracket(adv, bracket_rubric, public_picks=public, contrarian_weight=5.0)
    # With heavy contrarian weight, the champion pick should at least sometimes flip.
    assert (
        chalk.picks_by_round["W"] != contra.picks_by_round["W"]
        or chalk.picks_by_round["F"] != contra.picks_by_round["F"]
    )
