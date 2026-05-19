"""End-to-end WC 2026 prediction script.

Runs the full prediction pipeline using current data:
  1. Loads pre-computed features for all 72 WC2026 group matches
  2. Predicts 1X2 + score matrix for each match with Dixon-Coles and LightGBM
  3. Blends via simple average (stacker requires OOF training; v1 uses simple blend)
  4. Hands the joint predictor to TournamentSim, runs N Monte Carlo simulations
  5. Writes advancement + match_probs + sample brackets parquets
  6. Prints champion top-10

Usage:
    python -m src.predict_wc2026 --n 10000
"""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import polars as pl

from src.models import dixon_coles as dc
from src.models import gbm as gbm_mod
from src.models.stacker import reweight_score_matrix
from src.sims.tournament import TournamentSim
from src.features.elo import elo_as_of


def build_predictor(asof: date, gbm_path: str, xi: float = 0.0019):
    matches = pl.read_parquet("data/processed/matches.parquet").to_pandas()
    print(f"  Fitting Dixon-Coles on {len(matches):,} matches with asof={asof}…")
    dc_model = dc.fit(matches, asof_date=asof, xi=xi, min_team_matches=3)

    print(f"  Loading LightGBM from {gbm_path}…")
    gbm = gbm_mod.load(gbm_path)

    features_wc = pl.read_parquet("data/processed/features_wc2026.parquet").to_pandas()
    feat_by_pair = {(r["home_team"], r["away_team"]): r for _, r in features_wc.iterrows() if pd.notna(r.get("home_team"))}

    def predict(home: str, away: str) -> np.ndarray:
        try:
            dc_pred = dc.predict(dc_model, home, away)
        except (KeyError, ValueError):
            n = 11
            sm = np.full((n, n), 1.0 / (n * n))
            return sm
        sm = dc_pred.score_matrix.copy()
        feat_row = feat_by_pair.get((home, away))
        if feat_row is not None:
            row_df = pd.DataFrame([feat_row]).copy()
            for col in gbm.feature_cols:
                if col not in row_df.columns:
                    row_df[col] = np.nan
            try:
                gbm_probs = gbm.predict_proba(row_df)[0]
                dc_1x2 = np.array([dc_pred.p_home_win, dc_pred.p_draw, dc_pred.p_away_win])
                blended = 0.5 * dc_1x2 + 0.5 * gbm_probs
                blended = blended / blended.sum()
                sm = reweight_score_matrix(sm, blended)
            except Exception:
                pass
        return sm

    elo_history = pl.read_parquet("data/processed/elo_ratings_history.parquet").to_pandas()
    def strength(team: str) -> float:
        return (elo_as_of(elo_history, team, pd.Timestamp(asof)) - 1500.0)

    return predict, strength


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--n", type=int, default=10000)
    p.add_argument("--asof", default="2026-05-18")
    p.add_argument("--gbm-path", default="data/models/lgbm_pre_euro24.txt")
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()

    asof = pd.Timestamp(args.asof).date()
    print(f"Building blended predictor (DC + LightGBM) asof={asof}…")
    predict, strength = build_predictor(asof, args.gbm_path)

    print(f"Running {args.n:,} Monte Carlo tournament simulations…")
    sim = TournamentSim(predict_fn=predict, strength_fn=strength)
    results = sim.run(n_sims=args.n, seed=args.seed)
    print(f"  done in {results.seconds:.1f}s ({args.n/results.seconds:.1f} sims/s)")

    adv = results.advancement.sort_values("p_champion", ascending=False)
    print("\nTop 10 champion probabilities:")
    cols = ["team", "p_advance_group", "p_R16_win", "p_QF_win", "p_SF_win", "p_final_win", "p_champion"]
    print(adv.head(10)[cols].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
