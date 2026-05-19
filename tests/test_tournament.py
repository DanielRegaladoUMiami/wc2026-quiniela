"""Tournament simulator tests — fast smoke + tiebreaker logic."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.sims.bracket_2026 import GROUPS
from src.sims.tournament import (
    STAGES_ORDER,
    TournamentSim,
    _apply_tiebreakers,
    _build_uniform_predictor,
)


def test_uniform_simulator_advancement_counts() -> None:
    sim = TournamentSim(_build_uniform_predictor(max_goals=4))
    res = sim.run(n_sims=200, seed=123, save=False)

    # 48 teams in output
    assert len(res.advancement) == 48

    # champion probs sum to ~1
    assert abs(res.advancement["p_champion"].sum() - 1.0) < 1e-9

    # per-sim consistency: count from sample_brackets
    # Use one sim to verify exact stage cardinalities
    rng = np.random.default_rng(7)
    out = sim.simulate_tournament(rng)
    adv = out["advancement"]
    # Stage counts:
    # "group" = eliminated in groups (48 - 32 = 16)
    # "R32" = reached R32 but lost there
    # plus deeper stages
    reached_at_least: dict[str, int] = {}
    for st in STAGES_ORDER:
        idx = STAGES_ORDER.index(st)
        deeper = [s for s in STAGES_ORDER if STAGES_ORDER.index(s) >= idx]
        reached_at_least[st] = sum(1 for v in adv.values() if v in deeper)

    assert reached_at_least["R32"] == 32
    assert reached_at_least["R16"] == 16
    assert reached_at_least["QF"] == 8
    assert reached_at_least["SF"] == 4
    assert reached_at_least["final"] == 2
    assert reached_at_least["champion"] == 1


def test_uniform_match_probs_unbiased() -> None:
    sim = TournamentSim(_build_uniform_predictor(max_goals=4))
    res = sim.run(n_sims=200, seed=42, save=False)
    # group matches under uniform: P(home_win) ~ P(away_win), draw ~ 1/5 (5 diagonals / 25)
    g = res.match_probs[res.match_probs["num"] <= 72]
    assert ((g["p_home_win"] + g["p_draw"] + g["p_away_win"]) - 1.0).abs().max() < 1e-9
    # weak sanity: home/away wins close to each other on average
    assert abs(g["p_home_win"].mean() - g["p_away_win"].mean()) < 0.05


def test_tiebreaker_points_gd_gf() -> None:
    df = pd.DataFrame([
        {"group": "X", "team": "A", "PTS": 6, "GF": 4, "GA": 2, "GD": 2},
        {"group": "X", "team": "B", "PTS": 6, "GF": 5, "GA": 2, "GD": 3},
        {"group": "X", "team": "C", "PTS": 3, "GF": 2, "GA": 4, "GD": -2},
        {"group": "X", "team": "D", "PTS": 0, "GF": 0, "GA": 3, "GD": -3},
    ])
    out = _apply_tiebreakers(df, [], np.random.default_rng(0))
    assert out.iloc[0]["team"] == "B"  # higher GD breaks tie
    assert out.iloc[1]["team"] == "A"
    assert out.iloc[2]["team"] == "C"
    assert out.iloc[3]["team"] == "D"


def test_tiebreaker_head_to_head() -> None:
    # A and B tied on PTS=6, GD=2, GF=4; H2H A beat B 2-1 -> A first
    df = pd.DataFrame([
        {"group": "X", "team": "A", "PTS": 6, "GF": 4, "GA": 2, "GD": 2},
        {"group": "X", "team": "B", "PTS": 6, "GF": 4, "GA": 2, "GD": 2},
        {"group": "X", "team": "C", "PTS": 0, "GF": 1, "GA": 5, "GD": -4},
    ])
    h2h = [("A", "B", 2, 1)]
    out = _apply_tiebreakers(df, h2h, np.random.default_rng(0))
    assert out.iloc[0]["team"] == "A"
    assert out.iloc[1]["team"] == "B"


def test_groups_topology() -> None:
    assert len(GROUPS) == 12
    assert sum(len(v) for v in GROUPS.values()) == 48
