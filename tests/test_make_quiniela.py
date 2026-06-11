"""End-to-end test for the quiniela deliverable on a real tracked sim run."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.strategy.bracket_picks import normalize_advancement
from src.strategy.make_quiniela import build_entry_inputs, latest_sim_run, make_quiniela

ROOT = Path(__file__).resolve().parents[1]
RUBRICS = ROOT / "configs" / "rubrics"

pytestmark = pytest.mark.skipif(
    not list((ROOT / "data" / "sims").glob("sim_run_*")),
    reason="no tracked sim run on disk",
)


@pytest.fixture(scope="module")
def sim_run() -> Path:
    return latest_sim_run(ROOT / "data" / "sims")


def test_normalize_advancement_real_sim_schema(sim_run):
    adv = pd.read_parquet(sim_run / "advancement.parquet")
    norm = normalize_advancement(adv)
    for col in ("p_advance", "p_R16", "p_QF", "p_SF", "p_final", "p_champion"):
        assert col in norm.columns
    # Reach probabilities must be monotone non-increasing through the bracket.
    assert (norm["p_advance"] >= norm["p_R16"]).all()
    assert (norm["p_R16"] >= norm["p_QF"]).all()
    assert (norm["p_champion"] <= norm["p_final"] + 1e-9).all()


def test_build_entry_inputs_covers_group_stage(sim_run):
    mp = pd.read_parquet(sim_run / "match_probs.parquet")
    inputs = build_entry_inputs(mp)
    assert len(inputs) == 72
    assert {"match_num", "home_team", "away_team", "score_matrix"} <= set(inputs.columns)
    # Score matrices must reproduce the sim 1X2, not the polluted goal columns.
    row = inputs.iloc[0]
    sm = row["score_matrix"]
    assert sm.sum() == pytest.approx(1.0)
    n = sm.shape[0]
    p_home = (sm * np.tril(np.ones((n, n)), k=-1)).sum()
    assert p_home == pytest.approx(row["p_home_win"], abs=1e-6)


def test_make_quiniela_end_to_end(sim_run, tmp_path):
    out_dir = make_quiniela(
        sim_run=sim_run,
        rubric_path=RUBRICS / "fifa_quiniela_mx.yaml",
        bracket_rubric_path=RUBRICS / "espn_bracket.yaml",
        out_root=tmp_path,
        n_entries=3,
    )
    assert (out_dir / "quiniela.json").exists()
    assert (out_dir / "entries.csv").exists()
    assert (out_dir / "quiniela.md").exists()

    payload = json.loads((out_dir / "quiniela.json").read_text())
    assert payload["sim_run"] == sim_run.name
    assert len(payload["entries"]) == 3
    labels = [e["label"] for e in payload["entries"]]
    assert labels == ["chalk", "moderate_contrarian", "high_variance"]
    for e in payload["entries"]:
        assert len(e["picks"]) == 72
        assert e["expected_points"] > 0
        for p in e["picks"]:
            assert p["result"] in {"H", "D", "A"}
            assert p["totals"] in {"OVER", "UNDER"}

    # The schema-mismatch regression: every round must fill, not just the champion.
    for variant in ("chalk", "contrarian"):
        rounds = payload["bracket"][variant]["picks_by_round"]
        slot_counts = [len(rounds[r]) for r in ("R32", "R16", "QF", "SF", "F", "W")]
        assert slot_counts == [32, 16, 8, 4, 2, 1]

    csv = pd.read_csv(out_dir / "entries.csv")
    assert len(csv) == 3 * 72
