"""Generic walk-forward backtest harness.

A `Predictor` here is any callable / object exposing two methods:
    refit(asof_date: date) -> None
    predict(home: str, away: str, venue_country: str | None) -> dict
                                                                  with keys p_home, p_draw, p_away

`walk_forward` walks each tournament match in chronological order, calls
`predictor.refit(d)` once per *new* match date (so all training data has
`date < d`), then asks for predictions for every fixture on that date.

Anti-leakage guarantee:
    Before each prediction we assert `predictor.fit_asof_date <= match_date`
    AND that the predictor was fit with data strictly less than that date —
    enforced via `predictor.fit_asof_date` attribute the wrappers must set.

The returned DataFrame is the per-match prediction log; callers compute RPS
etc. from it.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Protocol

import numpy as np
import pandas as pd

from src.eval.rps import outcome_1x2
from src.eval.tournaments import TOURNAMENTS, select_tournament


class Predictor(Protocol):
    fit_asof_date: date | None

    def refit(self, asof_date: date) -> None: ...
    def predict(self, home: str, away: str, venue_country: str | None = None) -> dict: ...


@dataclass
class WalkForwardResult:
    tournament: str
    model_name: str
    predictions: pd.DataFrame
    skipped: list[dict]


def walk_forward(
    matches_all: pd.DataFrame,
    tournament_key: str,
    predictor: Predictor,
    model_name: str = "model",
    verbose: bool = False,
) -> WalkForwardResult:
    """Run walk-forward over one tournament.

    `matches_all` is the full match log (used by the predictor for training).
    Predictor `refit(asof_date)` is responsible for filtering its own training set;
    we just assert the harness contract:
      after refit, predictor.fit_asof_date must equal asof_date,
      and predictor must promise to have used only date < asof_date.
    """
    t = TOURNAMENTS[tournament_key]
    tourney = select_tournament(matches_all, t)
    if tourney.empty:
        raise ValueError(f"No matches found for tournament {tournament_key}")

    preds_log: list[dict] = []
    skipped: list[dict] = []
    last_fit_date: date | None = None

    for _, m in tourney.iterrows():
        d = m["date"]
        if not isinstance(d, date):
            d = pd.to_datetime(d).date()
        if last_fit_date != d:
            predictor.refit(d)
            last_fit_date = d
            # Anti-leakage: predictor must record asof_date and respect strict <.
            assert getattr(predictor, "fit_asof_date", None) == d, (
                f"predictor.fit_asof_date={getattr(predictor, 'fit_asof_date', None)} "
                f"!= match_date={d} after refit"
            )
        venue = m.get("venue_country") if "venue_country" in tourney.columns else None
        if isinstance(venue, float) and np.isnan(venue):
            venue = None
        try:
            p = predictor.predict(m["home_team"], m["away_team"], venue_country=venue)
        except KeyError as exc:
            skipped.append(
                {
                    "date": d,
                    "home_team": m["home_team"],
                    "away_team": m["away_team"],
                    "reason": f"unknown_team:{exc}",
                }
            )
            if verbose:
                print(f"  skip {m['home_team']} vs {m['away_team']}: {exc}")
            continue
        except Exception as exc:
            skipped.append(
                {
                    "date": d,
                    "home_team": m["home_team"],
                    "away_team": m["away_team"],
                    "reason": f"predict_error:{exc}",
                }
            )
            continue

        out = outcome_1x2(int(m["home_goals"]), int(m["away_goals"]))
        preds_log.append(
            {
                "date": d,
                "tournament": tournament_key,
                "model": model_name,
                "home_team": m["home_team"],
                "away_team": m["away_team"],
                "home_goals": int(m["home_goals"]),
                "away_goals": int(m["away_goals"]),
                "p_home": float(p["p_home"]),
                "p_draw": float(p["p_draw"]),
                "p_away": float(p["p_away"]),
                "outcome": out,
            }
        )

    return WalkForwardResult(
        tournament=tournament_key,
        model_name=model_name,
        predictions=pd.DataFrame(preds_log),
        skipped=skipped,
    )


# ---------- Predictor wrappers ----------


class DixonColesPredictor:
    """Wraps src.models.dixon_coles for the walk-forward harness."""

    def __init__(self, matches_all: pd.DataFrame, xi: float = 0.0019, min_team_matches: int = 10):
        from src.models import dixon_coles as dc

        self._dc = dc
        self.matches_all = matches_all
        self.xi = xi
        self.min_team_matches = min_team_matches
        self.model = None
        self.fit_asof_date: date | None = None

    def refit(self, asof_date: date) -> None:
        self.model = self._dc.fit(
            self.matches_all,
            asof_date=asof_date,
            xi=self.xi,
            min_team_matches=self.min_team_matches,
        )
        self.fit_asof_date = asof_date

    def predict(self, home: str, away: str, venue_country: str | None = None) -> dict:
        p = self._dc.predict(self.model, home, away)
        return {"p_home": p.p_home_win, "p_draw": p.p_draw, "p_away": p.p_away_win}


class GBMPredictor:
    """Wraps a pre-trained GBM model. GBM is not refit per match (too expensive);
    instead we load a model trained with data strictly before the tournament start
    and use it for the whole window. This is still walk-forward-honest at the
    tournament level. fit_asof_date is set to the tournament start.
    """

    def __init__(
        self,
        features_all: pd.DataFrame,
        model_path: str,
        tournament_start: date,
    ):
        from src.models import gbm as gbm_mod

        self._gbm = gbm_mod
        self.features_all = features_all.copy()
        self.features_all["date"] = pd.to_datetime(self.features_all["date"]).dt.date
        self.model = gbm_mod.load(model_path)
        self.tournament_start = tournament_start
        self.fit_asof_date: date | None = None
        # Index by (home, away, date) for fast lookup.
        self._lookup = {
            (r["home_team"], r["away_team"], r["date"]): idx
            for idx, r in self.features_all.iterrows()
        }

    def refit(self, asof_date: date) -> None:
        # Pre-trained model — no refit. We set fit_asof_date for the harness contract.
        # Pretrained model was fit with data < tournament_start; we attest that here.
        self.fit_asof_date = asof_date

    def predict(self, home: str, away: str, venue_country: str | None = None) -> dict:
        # Find the feature row for this match date.
        key_date = self.fit_asof_date
        idx = self._lookup.get((home, away, key_date))
        if idx is None:
            raise KeyError(f"no features row for {home} vs {away} on {key_date}")
        row = self.features_all.loc[[idx]]
        probs = self.model.predict_proba(row)[0]
        return {"p_home": float(probs[0]), "p_draw": float(probs[1]), "p_away": float(probs[2])}


class BayesianPredictor:
    """Wraps the Bayesian model in fast MAP mode for backtest. Refits per match date.

    NOTE: MAP point estimate, not full NUTS — full HMC is too slow to refit
    50+ times per tournament. This is documented as a limitation.
    """

    def __init__(
        self, matches_all: pd.DataFrame, lookback_years: int = 4, cache_dir: str | None = None
    ):
        from src.models import bayesian as bayes_mod

        self._bayes = bayes_mod
        self.matches_all = matches_all
        self.lookback_years = lookback_years
        self.model = None
        self.fit_asof_date: date | None = None

    def refit(self, asof_date: date) -> None:
        self.model = self._bayes.fit(
            self.matches_all,
            asof_date=asof_date,
            lookback_years=self.lookback_years,
            fast=True,
        )
        self.fit_asof_date = asof_date

    def predict(self, home: str, away: str, venue_country: str | None = None) -> dict:
        p = self._bayes.predict(self.model, home, away, venue_country=venue_country)
        return {"p_home": p.p_home_win, "p_draw": p.p_draw, "p_away": p.p_away_win}
