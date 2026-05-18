"""Fast-mode tests for the hierarchical Bayesian Poisson model.

These run with `fast=True` (MAP) so the suite stays under ~30s in CI.
"""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
import pytest

from src.models.bayesian import BayesianModel, fit, predict, predict_many


def _synthetic_matches(seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    teams = ["Strong", "Mid", "Weak", "Other1", "Other2"]
    strength = {"Strong": 1.2, "Mid": 0.0, "Other1": 0.1, "Other2": -0.1, "Weak": -1.2}
    rows = []
    start = date(2022, 1, 1)
    for i in range(240):
        h, a = rng.choice(teams, size=2, replace=False)
        lam_h = np.exp(0.1 + strength[h] - strength[a] + 0.2)
        lam_a = np.exp(0.1 + strength[a] - strength[h])
        rows.append(
            {
                "date": pd.Timestamp(start) + pd.Timedelta(days=int(i * 3)),
                "home_team": h,
                "away_team": a,
                "home_goals": int(rng.poisson(lam_h)),
                "away_goals": int(rng.poisson(lam_a)),
                "venue_country": "United States",
            }
        )
    return pd.DataFrame(rows)


@pytest.fixture(scope="module")
def fitted_model() -> BayesianModel:
    matches = _synthetic_matches()
    return fit(
        matches,
        asof_date=date(2024, 1, 1),
        lookback_years=4,
        fast=True,
        min_team_matches=5,
    )


def test_probs_sum_to_one(fitted_model: BayesianModel) -> None:
    pred = predict(fitted_model, "Strong", "Weak", venue_country="United States")
    total = pred.p_home_win + pred.p_draw + pred.p_away_win
    assert abs(total - 1.0) < 1e-3


def test_expected_goals_positive(fitted_model: BayesianModel) -> None:
    pred = predict(fitted_model, "Strong", "Weak", venue_country="United States")
    assert pred.expected_home_goals > 0.0
    assert pred.expected_away_goals > 0.0


def test_stronger_beats_weaker(fitted_model: BayesianModel) -> None:
    pred = predict(fitted_model, "Strong", "Weak", venue_country="United States")
    assert pred.p_home_win > pred.p_away_win
    assert pred.expected_home_goals > pred.expected_away_goals


def test_score_matrix_normalized(fitted_model: BayesianModel) -> None:
    pred = predict(fitted_model, "Strong", "Weak")
    assert abs(pred.score_matrix.sum() - 1.0) < 1e-6
    assert (pred.score_matrix >= 0).all()


def test_predict_many(fitted_model: BayesianModel) -> None:
    fixtures = pd.DataFrame(
        [
            {"home_team": "Strong", "away_team": "Weak", "venue_country": "Mexico"},
            {"home_team": "Mid", "away_team": "Other1", "venue_country": None},
        ]
    )
    out = predict_many(fitted_model, fixtures)
    assert len(out) == 2
    assert "p_home_win" in out.columns


def test_save_load(fitted_model: BayesianModel, tmp_path) -> None:
    path = tmp_path / "model.nc"
    fitted_model.save(path)
    loaded = BayesianModel.load(path)
    assert loaded.team_to_idx == fitted_model.team_to_idx
    p1 = predict(fitted_model, "Strong", "Weak")
    p2 = predict(loaded, "Strong", "Weak")
    assert abs(p1.p_home_win - p2.p_home_win) < 1e-6
