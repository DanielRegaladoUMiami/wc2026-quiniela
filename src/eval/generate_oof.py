"""Generate out-of-fold predictions from all base models on historical tournaments.

Output rows: (match_id, date, home_team, away_team, outcome,
              p_dc_h, p_dc_d, p_dc_a,
              p_gbm_h, p_gbm_d, p_gbm_a,
              p_bay_h, p_bay_d, p_bay_a)

Anti-leakage: each model is fit/loaded with cutoff < match_date. For speed we fit DC and
Bayesian ONCE per tournament (cutoff = tournament start), since refitting per match would
take days. GBM uses the pre-trained checkpoint that already saw a time-based training/valid
split. Each match within a tournament is technically still "before tournament info" from
the predictor's standpoint, since none of the models update from in-tournament results.

Tournaments included: WC18, WC22, Euro20, Euro24, Copa19, Copa21, Copa24.
"""

from __future__ import annotations

from datetime import date as Date
from pathlib import Path

import numpy as np
import pandas as pd
import polars as pl

from src.eval.rps import outcome_1x2
from src.models import bayesian as bay
from src.models import dixon_coles as dc
from src.models import gbm as gbm_mod


TOURNAMENTS = {
    "wc18":    {"start": Date(2018, 6, 14), "end": Date(2018, 7, 15), "competition": "FIFA World Cup"},
    "wc22":    {"start": Date(2022, 11, 20), "end": Date(2022, 12, 18), "competition": "FIFA World Cup"},
    "euro20":  {"start": Date(2021, 6, 11), "end": Date(2021, 7, 11), "competition": "UEFA Euro"},
    "euro24":  {"start": Date(2024, 6, 14), "end": Date(2024, 7, 14), "competition": "UEFA Euro"},
    "copa19":  {"start": Date(2019, 6, 14), "end": Date(2019, 7, 7),  "competition": "Copa América"},
    "copa21":  {"start": Date(2021, 6, 13), "end": Date(2021, 7, 10), "competition": "Copa América"},
    "copa24":  {"start": Date(2024, 6, 20), "end": Date(2024, 7, 14), "competition": "Copa América"},
}


def _select(matches: pd.DataFrame, t: dict) -> pd.DataFrame:
    m = matches.copy()
    m["date"] = pd.to_datetime(m["date"]).dt.date
    return m[
        (m["date"] >= t["start"])
        & (m["date"] <= t["end"])
        & m["competition"].str.contains(t["competition"], case=False, na=False)
    ].sort_values("date").reset_index(drop=True)


def _bay_or_fit(cutoff: Date) -> bay.BayesianModel | None:
    cache = Path(f"data/models/cache/bayesian_{cutoff}.nc")
    if cache.exists():
        return bay.BayesianModel.load(str(cache))
    cache.parent.mkdir(parents=True, exist_ok=True)
    matches = pl.read_parquet("data/processed/matches.parquet").to_pandas()
    try:
        model = bay.fit(matches, asof_date=cutoff, lookback_years=4, fast=True)
    except Exception as e:
        print(f"  Bayesian fit failed for {cutoff}: {e}")
        return None
    model.save(str(cache))
    return model


def generate(tournament_keys: list[str], out_path: str = "data/processed/oof_predictions.parquet") -> pd.DataFrame:
    matches = pl.read_parquet("data/processed/matches.parquet").to_pandas()
    features = pl.read_parquet("data/processed/features_match_level.parquet").to_pandas()
    features["date"] = pd.to_datetime(features["date"])

    # Use a single GBM trained pre-2018 to keep tournaments truly OOF
    gbm_cache = "data/models/cache/lgbm_pre_2018.txt"
    if not Path(gbm_cache).exists():
        Path(gbm_cache).parent.mkdir(parents=True, exist_ok=True)
        print("Training GBM with cutoff 2018-01-01…")
        model = gbm_mod.fit(features, train_end="2014-01-01", valid_end="2018-01-01")
        gbm_mod.save(model, gbm_cache)
    gbm = gbm_mod.load(gbm_cache)

    all_rows: list[dict] = []
    for tkey in tournament_keys:
        t = TOURNAMENTS[tkey]
        cutoff = t["start"]
        tourney = _select(matches, t)
        if tourney.empty:
            print(f"{tkey}: no matches")
            continue
        print(f"\n=== {tkey} (cutoff {cutoff}) — {len(tourney)} matches ===")

        # Fit DC at tournament cutoff (skip if covered by GBM cutoff)
        dc_cache = Path(f"data/models/cache/dc_{cutoff}.pkl")
        if dc_cache.exists():
            import pickle
            with open(dc_cache, "rb") as f:
                dc_model = pickle.load(f)
        else:
            print("  Fitting DC…")
            dc_model = dc.fit(matches, asof_date=cutoff, xi=0.0019, min_team_matches=5)
            dc_cache.parent.mkdir(parents=True, exist_ok=True)
            import pickle
            with open(dc_cache, "wb") as f:
                pickle.dump(dc_model, f)

        bay_model = _bay_or_fit(cutoff)

        for _, match in tourney.iterrows():
            mid = match["match_id"]
            home, away = match["home_team"], match["away_team"]
            try:
                hg = int(match["home_goals"])
                ag = int(match["away_goals"])
            except (TypeError, ValueError):
                continue
            outcome = outcome_1x2(hg, ag)

            # DC
            try:
                p = dc.predict(dc_model, home, away)
                p_dc = [p.p_home_win, p.p_draw, p.p_away_win]
            except Exception:
                p_dc = [None, None, None]

            # GBM
            feat_row = features[features["match_id"] == mid]
            p_gbm = [None, None, None]
            if not feat_row.empty:
                row = feat_row.copy()
                for col in gbm.feature_cols:
                    if col not in row.columns:
                        row[col] = np.nan
                try:
                    pg = gbm.predict_proba(row)[0]
                    p_gbm = list(pg)
                except Exception:
                    pass

            # Bayesian
            p_bay = [None, None, None]
            if bay_model is not None:
                try:
                    pb = bay.predict(bay_model, home, away, venue_country=None, max_goals=10)
                    p_bay = [pb.p_home_win, pb.p_draw, pb.p_away_win]
                except Exception:
                    pass

            all_rows.append(
                {
                    "match_id": mid, "date": match["date"], "tournament": tkey,
                    "home_team": home, "away_team": away,
                    "home_goals": hg, "away_goals": ag, "outcome": outcome,
                    "p_dc_h": p_dc[0], "p_dc_d": p_dc[1], "p_dc_a": p_dc[2],
                    "p_gbm_h": p_gbm[0], "p_gbm_d": p_gbm[1], "p_gbm_a": p_gbm[2],
                    "p_bay_h": p_bay[0], "p_bay_d": p_bay[1], "p_bay_a": p_bay[2],
                }
            )

        print(f"  collected {sum(1 for r in all_rows if r['tournament'] == tkey)} rows")

    df = pd.DataFrame(all_rows)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_path, compression="zstd")
    print(f"\nWrote {len(df):,} OOF rows → {out_path}")
    return df


def main() -> int:
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--tournaments", nargs="+", default=list(TOURNAMENTS))
    p.add_argument("--out", default="data/processed/oof_predictions.parquet")
    args = p.parse_args()
    generate(args.tournaments, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
