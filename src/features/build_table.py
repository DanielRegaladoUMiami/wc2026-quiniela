"""Build the match-level ML-ready feature table.

Joins:
  - matches (canonical)
  - elo_pre_match
  - team_form (twice: once for home, once for away side)
  - tournament importance + neutral flag

Produces `data/processed/features_match_level.parquet` with one row per historical match
plus a separate `data/processed/features_wc2026.parquet` for upcoming WC fixtures using
each team's most-recent form/Elo and the venue metadata from src/sims/bracket_2026.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import polars as pl

from src.eval.rps import outcome_1x2
from src.features.elo import compute_elo, elo_as_of
from src.sims.bracket_2026 import VENUES, all_fixtures_df


TOURNAMENT_IMPORTANCE = {
    "friendly": 1.0,
    "qualification": 2.0,
    "nations league": 2.5,
    "copa america": 3.0,
    "uefa euro": 3.5,
    "fifa world cup": 4.0,
}


def importance_weight(comp: str) -> float:
    c = (comp or "").lower()
    for k, v in TOURNAMENT_IMPORTANCE.items():
        if k in c:
            return v
    return 1.5


def _wide_form(form: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (home_form, away_form) frames keyed by match_id with prefixed columns."""
    home = form[form["side"] == "home"].drop(columns=["side", "team", "date"])
    away = form[form["side"] == "away"].drop(columns=["side", "team", "date"])
    home = home.add_prefix("h_").rename(columns={"h_match_id": "match_id"})
    away = away.add_prefix("a_").rename(columns={"a_match_id": "match_id"})
    return home, away


def build_historical() -> pd.DataFrame:
    matches = pl.read_parquet("data/processed/matches.parquet").to_pandas()
    elo_pre = pl.read_parquet("data/processed/elo_pre_match.parquet").to_pandas()
    form = pl.read_parquet("data/processed/team_form.parquet").to_pandas()

    matches["date"] = pd.to_datetime(matches["date"])
    matches = matches.dropna(subset=["home_goals", "away_goals"])
    matches["outcome"] = matches.apply(
        lambda r: outcome_1x2(int(r["home_goals"]), int(r["away_goals"])), axis=1
    )
    matches["total_goals"] = matches["home_goals"].astype(int) + matches["away_goals"].astype(int)
    matches["btts"] = ((matches["home_goals"] > 0) & (matches["away_goals"] > 0)).astype(int)
    matches["importance"] = matches["competition"].apply(importance_weight)

    elo_cols = elo_pre[["match_id", "home_elo_pre", "away_elo_pre", "p_home_win_elo"]]
    df = matches.merge(elo_cols, on="match_id", how="left")

    home_form, away_form = _wide_form(form)
    df = df.merge(home_form, on="match_id", how="left").merge(away_form, on="match_id", how="left")

    df["elo_diff"] = df["home_elo_pre"] - df["away_elo_pre"]
    for w in (5, 10, 20):
        df[f"form_diff_ppg_{w}"] = df[f"h_ppg_{w}"] - df[f"a_ppg_{w}"]
        df[f"form_diff_gd_{w}"] = df[f"h_gd_pm_{w}"] - df[f"a_gd_pm_{w}"]
    return df


def build_wc2026(historical: pd.DataFrame) -> pd.DataFrame:
    """One-row-per-WC2026-fixture frame with the *latest* features for each team."""
    fixtures = all_fixtures_df()
    venue_map = {v["key"]: v for v in VENUES}

    elo_history = pl.read_parquet("data/processed/elo_ratings_history.parquet").to_pandas()
    form = pl.read_parquet("data/processed/team_form.parquet").to_pandas()
    cutoff = fixtures["date"].min()

    # Latest known per-team form (most recent before cutoff)
    form = form[form["date"] < cutoff].sort_values("date")
    latest_form = form.groupby("team").tail(1).set_index("team")

    rows = []
    for r in fixtures.itertuples(index=False):
        venue = venue_map.get(r.venue, {})
        row = {
            "match_num": r.num,
            "date": r.date,
            "stage": r.stage,
            "group": r.group,
            "home_team": r.home,
            "away_team": r.away,
            "venue": r.venue,
            "venue_country": venue.get("country"),
            "venue_altitude_m": venue.get("altitude_m"),
            "venue_indoor": venue.get("indoor"),
        }
        if r.home and r.away:
            row["home_elo_pre"] = elo_as_of(elo_history, r.home, r.date)
            row["away_elo_pre"] = elo_as_of(elo_history, r.away, r.date)
            row["elo_diff"] = row["home_elo_pre"] - row["away_elo_pre"]
            for side, team in (("h_", r.home), ("a_", r.away)):
                if team in latest_form.index:
                    src = latest_form.loc[team]
                    for col in src.index:
                        if col in ("match_id", "team", "side", "date"):
                            continue
                        row[f"{side}{col}"] = src[col]
        rows.append(row)
    return pd.DataFrame(rows)


def main() -> int:
    out_dir = Path("data/processed")
    print("Building historical features…")
    hist = build_historical()
    hist.to_parquet(out_dir / "features_match_level.parquet", compression="zstd")
    print(f"  wrote {len(hist):,} rows × {hist.shape[1]} cols → features_match_level.parquet")

    print("Building WC2026 fixture features…")
    wc = build_wc2026(hist)
    wc.to_parquet(out_dir / "features_wc2026.parquet", compression="zstd")
    print(f"  wrote {len(wc):,} rows × {wc.shape[1]} cols → features_wc2026.parquet")
    print(f"  matches with known teams (group stage): {wc['home_team'].notna().sum()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
