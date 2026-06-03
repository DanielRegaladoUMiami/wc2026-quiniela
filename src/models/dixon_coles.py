"""Dixon-Coles bivariate Poisson model with exponential time decay.

Thin wrapper over `penaltyblog.models.DixonColesGoalModel`. We expose:
  - fit(matches, asof_date, xi) -> model
  - predict(model, home, away) -> dict with home_win/draw/away_win + score matrix
  - predict_many(model, fixtures) -> DataFrame of probabilities

`xi=0.0019` corresponds to a ~1-year half-life and is the value Dixon-Coles recommended;
`penaltyblog`'s `weights_dc_decay(xi, dates)` produces the exponential weights.

For backtesting we *must* call `fit` with `asof_date` so only past matches are used.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime

import numpy as np
import pandas as pd
import penaltyblog as pb


@dataclass
class DCPrediction:
    home_team: str
    away_team: str
    p_home_win: float
    p_draw: float
    p_away_win: float
    expected_home_goals: float
    expected_away_goals: float
    score_matrix: np.ndarray  # shape (max_g+1, max_g+1)

    def asdict(self) -> dict:
        return {
            "home_team": self.home_team,
            "away_team": self.away_team,
            "p_home_win": self.p_home_win,
            "p_draw": self.p_draw,
            "p_away_win": self.p_away_win,
            "expected_home_goals": self.expected_home_goals,
            "expected_away_goals": self.expected_away_goals,
        }


def _to_date(x: date | str | datetime) -> date:
    if isinstance(x, date) and not isinstance(x, datetime):
        return x
    if isinstance(x, datetime):
        return x.date()
    return datetime.fromisoformat(str(x)).date()


def fit(
    matches: pd.DataFrame,
    asof_date: date | str,
    xi: float = 0.0019,
    min_team_matches: int = 5,
) -> pb.models.DixonColesGoalModel:
    """Fit Dixon-Coles on matches strictly before `asof_date`.

    `matches` must have columns: date, home_team, away_team, home_goals, away_goals.
    Teams with fewer than `min_team_matches` in the training window are dropped to keep
    the optimizer well-conditioned.
    """
    asof = _to_date(asof_date)
    df = matches.copy()
    df["date"] = pd.to_datetime(df["date"]).dt.date
    df = df[df["date"] < asof].dropna(subset=["home_goals", "away_goals"])

    counts = pd.concat([df["home_team"], df["away_team"]]).value_counts()
    keep = counts[counts >= min_team_matches].index
    df = df[df["home_team"].isin(keep) & df["away_team"].isin(keep)].copy()

    if df.empty:
        raise ValueError(f"No training matches before {asof}")

    weights = pb.models.dixon_coles_weights(
        pd.to_datetime(df["date"]).to_numpy(),
        xi=xi,
        base_date=pd.Timestamp(asof),
    )

    model = pb.models.DixonColesGoalModel(
        df["home_goals"].astype(int).to_numpy(),
        df["away_goals"].astype(int).to_numpy(),
        df["home_team"].to_numpy(),
        df["away_team"].to_numpy(),
        weights=weights,
    )
    model.fit()
    return model


def predict(
    model: pb.models.DixonColesGoalModel,
    home_team: str,
    away_team: str,
    max_goals: int = 10,
) -> DCPrediction:
    """Predict one fixture. Returns 1X2 probabilities and full score matrix."""
    pred = model.predict(home_team, away_team, max_goals=max_goals)
    sm = np.zeros((max_goals + 1, max_goals + 1))
    for i in range(max_goals + 1):
        for j in range(max_goals + 1):
            sm[i, j] = pred.exact_score(i, j)
    sm /= sm.sum()
    goal_idx = np.arange(max_goals + 1)
    eh = float((goal_idx[:, None] * sm).sum())
    ea = float((goal_idx[None, :] * sm).sum())
    return DCPrediction(
        home_team=home_team,
        away_team=away_team,
        p_home_win=float(pred.home_win),
        p_draw=float(pred.draw),
        p_away_win=float(pred.away_win),
        expected_home_goals=eh,
        expected_away_goals=ea,
        score_matrix=sm,
    )


def predict_many(
    model: pb.models.DixonColesGoalModel,
    fixtures: Iterable[tuple[str, str]],
    max_goals: int = 10,
) -> pd.DataFrame:
    rows = []
    for h, a in fixtures:
        try:
            p = predict(model, h, a, max_goals=max_goals)
            rows.append(p.asdict())
        except Exception as exc:
            rows.append({"home_team": h, "away_team": a, "error": str(exc)})
    return pd.DataFrame(rows)
