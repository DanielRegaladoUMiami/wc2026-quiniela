"""Walk-forward backtest for a single tournament with anti-leakage enforcement.

Refits the chosen model after every matchday so each prediction only uses information
available before the match. Reports RPS and log-loss on 1X2 outcomes.

Usage:
    python -m src.eval.backtest_runner --tournament wc2022
    python -m src.eval.backtest_runner --tournament euro2024 --model dixon_coles
"""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import polars as pl

from src.eval.rps import log_loss_1x2, mean_rps, outcome_1x2
from src.models import dixon_coles as dc
from src.models import gbm as gbm_mod

MATCH_LOG = Path("data/processed/matches.parquet")


TOURNAMENTS = {
    "wc2018": {
        "competition_match": "FIFA World Cup",
        "year": 2018,
        "start": date(2018, 6, 14),
        "end": date(2018, 7, 15),
    },
    "wc2022": {
        "competition_match": "FIFA World Cup",
        "year": 2022,
        "start": date(2022, 11, 20),
        "end": date(2022, 12, 18),
    },
    "euro2024": {
        "competition_match": "UEFA Euro",
        "year": 2024,
        "start": date(2024, 6, 14),
        "end": date(2024, 7, 14),
    },
    "copa2024": {
        "competition_match": "Copa América",
        "year": 2024,
        "start": date(2024, 6, 20),
        "end": date(2024, 7, 14),
    },
}


def select_tournament(matches: pd.DataFrame, t: dict) -> pd.DataFrame:
    m = matches.copy()
    m["date"] = pd.to_datetime(m["date"]).dt.date
    return (
        m[
            (m["date"] >= t["start"])
            & (m["date"] <= t["end"])
            & m["competition"].str.contains(t["competition_match"], case=False, na=False)
        ]
        .sort_values("date")
        .reset_index(drop=True)
    )


def backtest_dixon_coles(matches: pd.DataFrame, tournament_key: str, xi: float = 0.0019) -> dict:
    t = TOURNAMENTS[tournament_key]
    tourney = select_tournament(matches, t)
    if tourney.empty:
        raise ValueError(f"No tournament matches found for {tournament_key}")
    print(f"Backtesting {tournament_key}: {len(tourney)} matches from {t['start']} to {t['end']}")

    # Walk-forward day by day
    probs = []
    outcomes = []
    preds_log = []
    model = None
    last_fit_date = None

    for _, match in tourney.iterrows():
        d = match["date"]
        if last_fit_date != d:
            model = dc.fit(matches, asof_date=d, xi=xi, min_team_matches=10)
            last_fit_date = d
        try:
            p = dc.predict(model, match["home_team"], match["away_team"])
        except KeyError as exc:
            print(f"  skip (unknown team) {match['home_team']} vs {match['away_team']}: {exc}")
            continue
        probs.append([p.p_home_win, p.p_draw, p.p_away_win])
        outcomes.append(outcome_1x2(int(match["home_goals"]), int(match["away_goals"])))
        preds_log.append(
            {
                "date": d,
                "home_team": match["home_team"],
                "away_team": match["away_team"],
                "home_goals": int(match["home_goals"]),
                "away_goals": int(match["away_goals"]),
                "p_home": p.p_home_win,
                "p_draw": p.p_draw,
                "p_away": p.p_away_win,
                "outcome": outcome_1x2(int(match["home_goals"]), int(match["away_goals"])),
            }
        )

    probs_arr = np.asarray(probs)
    outcomes_arr = np.asarray(outcomes)
    return {
        "tournament": tournament_key,
        "n_matches": len(probs),
        "rps": mean_rps(probs_arr, outcomes_arr),
        "log_loss": log_loss_1x2(probs_arr, outcomes_arr),
        "accuracy": float((probs_arr.argmax(axis=1) == outcomes_arr).mean()),
        "predictions": pd.DataFrame(preds_log),
    }


def backtest_gbm(features: pd.DataFrame, tournament_key: str, model_path: str) -> dict:
    t = TOURNAMENTS[tournament_key]
    tourney = select_tournament(features, t)
    if tourney.empty:
        raise ValueError(f"No tournament matches in features for {tournament_key}")
    model = gbm_mod.load(model_path)
    probs = model.predict_proba(tourney)
    outcomes = tourney["outcome"].astype(int).to_numpy()
    return {
        "tournament": tournament_key,
        "n_matches": len(tourney),
        "rps": mean_rps(probs, outcomes),
        "log_loss": log_loss_1x2(probs, outcomes),
        "accuracy": float((probs.argmax(axis=1) == outcomes).mean()),
        "predictions": pd.DataFrame(
            {
                "date": tourney["date"].values,
                "home_team": tourney["home_team"].values,
                "away_team": tourney["away_team"].values,
                "home_goals": tourney["home_goals"].values,
                "away_goals": tourney["away_goals"].values,
                "p_home": probs[:, 0],
                "p_draw": probs[:, 1],
                "p_away": probs[:, 2],
                "outcome": outcomes,
            }
        ),
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--tournament", choices=list(TOURNAMENTS), default="wc2022")
    p.add_argument("--model", choices=["dixon_coles", "gbm"], default="dixon_coles")
    p.add_argument("--xi", type=float, default=0.0019)
    p.add_argument("--gbm-path", default="data/models/lgbm_pre_wc22.txt")
    p.add_argument("--save", action="store_true")
    args = p.parse_args()

    if args.model == "dixon_coles":
        matches = pl.read_parquet(MATCH_LOG).to_pandas()
        res = backtest_dixon_coles(matches, args.tournament, xi=args.xi)
    elif args.model == "gbm":
        feats = pl.read_parquet("data/processed/features_match_level.parquet").to_pandas()
        res = backtest_gbm(feats, args.tournament, args.gbm_path)
    else:
        raise ValueError(args.model)

    print(f"\nTournament: {res['tournament']}")
    print(f"Matches:    {res['n_matches']}")
    print(f"RPS:        {res['rps']:.4f}   (target < 0.21, uniform baseline ≈ 0.222)")
    print(f"Log loss:   {res['log_loss']:.4f}")
    print(f"Accuracy:   {res['accuracy']:.3f}")

    if args.save:
        out = Path("data/sims") / f"backtest_{args.model}_{args.tournament}.parquet"
        out.parent.mkdir(parents=True, exist_ok=True)
        res["predictions"].to_parquet(out)
        print(f"Predictions → {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
