"""Tests for the walk-forward backtest harness.

Key tests:
  1. Anti-leakage: if a predictor was fit with `asof_date` *after* the match date,
     the harness assertion must fire.
  2. Anti-leakage (data side): if we inject a feature that equals the future
     outcome, the harness still enforces the temporal filter — we test this by
     building a leak-prone predictor that ignores the asof_date and verifying
     the assertion catches it.
  3. asof_date filter: a synthetic predictor that records what it saw must only
     see rows with date < asof_date.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta

import numpy as np
import pandas as pd
import pytest

from src.eval.tournaments import TOURNAMENTS
from src.eval.walk_forward import walk_forward


def _toy_match_log() -> pd.DataFrame:
    """A small toy tournament inside a real TOURNAMENTS slot (wc22 dates)."""
    t = TOURNAMENTS["wc22"]
    start = t["start"]
    # Historical training rows + 4 tournament rows.
    rows = []
    # 200 fake training matches before start.
    rng = np.random.default_rng(0)
    teams = ["A", "B", "C", "D"]
    for i in range(200):
        d = start - timedelta(days=int(rng.integers(30, 365)))
        h, a = rng.choice(teams, size=2, replace=False)
        hg, ag = int(rng.integers(0, 4)), int(rng.integers(0, 4))
        rows.append(
            {
                "match_id": f"train_{i}",
                "date": d,
                "competition": "Friendly",
                "stage": None,
                "home_team": h,
                "away_team": a,
                "home_goals": hg,
                "away_goals": ag,
                "neutral_venue": False,
                "venue_country": None,
            }
        )
    # 4 tournament matches.
    for i, (d_off, h, a, hg, ag) in enumerate(
        [
            (0, "A", "B", 2, 1),
            (1, "C", "D", 0, 0),
            (2, "A", "C", 1, 2),
            (3, "B", "D", 3, 1),
        ]
    ):
        rows.append(
            {
                "match_id": f"t_{i}",
                "date": start + timedelta(days=d_off),
                "competition": "FIFA World Cup",
                "stage": "Group",
                "home_team": h,
                "away_team": a,
                "home_goals": hg,
                "away_goals": ag,
                "neutral_venue": True,
                "venue_country": "Qatar",
            }
        )
    return pd.DataFrame(rows)


@dataclass
class RecorderPredictor:
    """A predictor that records what training data it 'saw' at each refit."""

    matches_all: pd.DataFrame
    fit_asof_date: date | None = None
    seen_max_dates: list[date] = field(default_factory=list)
    cheat: bool = False  # if True, sets fit_asof_date to wrong value

    def refit(self, asof_date: date) -> None:
        if self.cheat:
            # Simulate a leaky predictor — pretend we fit at the match date but
            # actually used data up to and including the match date.
            self.fit_asof_date = asof_date - timedelta(days=1)
            return
        df = self.matches_all.copy()
        df["date"] = pd.to_datetime(df["date"]).dt.date
        train = df[df["date"] < asof_date]
        self.seen_max_dates.append(train["date"].max())
        self.fit_asof_date = asof_date

    def predict(self, home, away, venue_country=None):
        return {"p_home": 1 / 3, "p_draw": 1 / 3, "p_away": 1 / 3}


def test_walk_forward_filters_strictly_before_match_date():
    matches = _toy_match_log()
    pred = RecorderPredictor(matches_all=matches)
    res = walk_forward(matches, "wc22", pred, model_name="recorder")
    assert len(res.predictions) == 4
    # Every recorded max-training-date must be strictly < the corresponding match date.
    tourney_dates = sorted(set(res.predictions["date"]))
    for match_date, max_train_date in zip(tourney_dates, pred.seen_max_dates, strict=False):
        assert max_train_date < match_date, (
            f"Training data leaked: saw date {max_train_date} >= match date {match_date}"
        )


def test_walk_forward_anti_leakage_assertion_fires():
    """If predictor.fit_asof_date drifts from match_date, the harness must assert."""
    matches = _toy_match_log()
    pred = RecorderPredictor(matches_all=matches, cheat=True)
    with pytest.raises(AssertionError):
        walk_forward(matches, "wc22", pred, model_name="cheater")


def test_walk_forward_future_outcome_feature_detected():
    """Synthetic test: a predictor that builds a feature using a match's own outcome
    must still respect the harness's asof_date contract. We simulate this by having
    the leaky predictor set fit_asof_date past the actual match date — the assertion
    catches it.
    """
    matches = _toy_match_log()

    class FutureLeakPredictor:
        fit_asof_date: date | None = None

        def refit(self, asof_date):
            # Pretend we trained on data up to TOMORROW (post-match leak).
            self.fit_asof_date = asof_date + timedelta(days=1)

        def predict(self, h, a, venue_country=None):
            return {"p_home": 0.9, "p_draw": 0.05, "p_away": 0.05}

    with pytest.raises(AssertionError):
        walk_forward(matches, "wc22", FutureLeakPredictor(), model_name="leak")
