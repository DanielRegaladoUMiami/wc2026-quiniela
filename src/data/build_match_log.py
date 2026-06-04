"""Build the canonical unified match log from all ingested sources.

Output: `data/processed/matches.parquet` with one row per international match, deduped on
(date, home_team, away_team). For Day 1 only the Kaggle martj42 source is wired in;
StatsBomb / FBref / RSSSF merges land in Day 3-4.

Canonical schema:
    match_id, date, competition, stage, home_team, away_team,
    home_goals, away_goals, neutral_venue, venue_city, venue_country,
    venue_altitude_m, home_xg, away_xg, source, statsbomb_match_id
"""

from __future__ import annotations

import hashlib
import os
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import polars as pl

from src.data.team_names import CANONICAL

KAGGLE_RESULTS = Path("data/raw/matches/kaggle_martj42/results.csv")
OUT = Path("data/processed/matches.parquet")

# Fail the build if the raw results source hasn't been refreshed within this many days.
# International matches are sparse (they only happen in FIFA windows), so we guard on
# *source-refresh* recency — "did we actually re-pull?" — rather than match-date recency,
# which legitimately lags by weeks between windows and would false-alarm.
MAX_SOURCE_AGE_DAYS = int(os.environ.get("WC2026_MAX_SOURCE_AGE_DAYS", "3"))


def assert_source_fresh() -> None:
    """Loudly refuse to build the canonical log from a stale source pull.

    Bypass with WC2026_ALLOW_STALE=1 (e.g. offline reproducibility runs).
    """
    if os.environ.get("WC2026_ALLOW_STALE") == "1":
        print("freshness check skipped (WC2026_ALLOW_STALE=1)")
        return
    if not KAGGLE_RESULTS.exists():
        return  # load_kaggle_martj42 raises a clearer error downstream
    mtime = datetime.fromtimestamp(KAGGLE_RESULTS.stat().st_mtime, tz=UTC)
    age_days = (datetime.now(UTC) - mtime).total_seconds() / 86400
    if age_days > MAX_SOURCE_AGE_DAYS:
        raise SystemExit(
            f"STALE SOURCE: {KAGGLE_RESULTS} last refreshed {age_days:.1f}d ago "
            f"(> {MAX_SOURCE_AGE_DAYS}d). Run `python -m src.data.fetch_kaggle_martj42` first, "
            f"or set WC2026_ALLOW_STALE=1 to bypass."
        )
    print(f"source freshness OK: results.csv refreshed {age_days:.1f}d ago")


CANONICAL_COLS = [
    "match_id",
    "date",
    "competition",
    "stage",
    "home_team",
    "away_team",
    "home_goals",
    "away_goals",
    "neutral_venue",
    "venue_city",
    "venue_country",
    "venue_altitude_m",
    "home_xg",
    "away_xg",
    "source",
    "statsbomb_match_id",
]


def _make_match_id(date: str, home: str, away: str) -> str:
    return hashlib.sha1(f"{date}|{home}|{away}".encode()).hexdigest()[:16]


def load_kaggle_martj42() -> pl.DataFrame:
    if not KAGGLE_RESULTS.exists():
        raise FileNotFoundError(
            f"{KAGGLE_RESULTS} missing. Run `python -m src.data.fetch_kaggle_martj42` first."
        )
    # Pandas handles the mixed-quoting / TRUE-FALSE booleans in this file more leniently than Polars.
    pdf = pd.read_csv(KAGGLE_RESULTS, dtype={"neutral": "string", "date": "string"})
    df = pl.from_pandas(pdf)
    return (
        df.rename(
            {
                "home_score": "home_goals",
                "away_score": "away_goals",
                "tournament": "competition",
                "city": "venue_city",
                "country": "venue_country",
                "neutral": "neutral_venue",
            }
        )
        .with_columns(
            pl.col("neutral_venue")
            .str.to_lowercase()
            .is_in(["true", "1", "t"])
            .alias("neutral_venue"),
            pl.col("date").alias("date_str"),
            pl.col("date").str.strptime(pl.Date, "%Y-%m-%d").alias("date"),
            # Normalize team names to the canonical (bracket) spelling so the log,
            # features and market odds all line up — see src/data/team_names.py.
            pl.col("home_team").replace(CANONICAL).alias("home_team"),
            pl.col("away_team").replace(CANONICAL).alias("away_team"),
        )
        .with_columns(
            pl.struct(["date_str", "home_team", "away_team"])
            .map_elements(
                lambda s: _make_match_id(s["date_str"], s["home_team"], s["away_team"]),
                return_dtype=pl.Utf8,
            )
            .alias("match_id"),
            pl.lit(None, dtype=pl.Utf8).alias("stage"),
            pl.lit(None, dtype=pl.Float64).alias("venue_altitude_m"),
            pl.lit(None, dtype=pl.Float64).alias("home_xg"),
            pl.lit(None, dtype=pl.Float64).alias("away_xg"),
            pl.lit("kaggle_martj42").alias("source"),
            pl.lit(None, dtype=pl.Utf8).alias("statsbomb_match_id"),
        )
        .select(CANONICAL_COLS)
    )


def build() -> pl.DataFrame:
    frames = [load_kaggle_martj42()]
    matches = pl.concat(frames, how="vertical")
    matches = matches.unique(subset=["match_id"], keep="first").sort("date")
    return matches


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    assert_source_fresh()
    matches = build()
    matches.write_parquet(OUT, compression="zstd")
    played = matches.filter(pl.col("home_goals").is_not_null())
    print(f"Wrote {len(matches):,} matches → {OUT}")
    print(f"Date range: {matches['date'].min()} → {matches['date'].max()}")
    print(
        f"Played: {len(played):,} (latest played: {played['date'].max()}) | upcoming: {len(matches) - len(played):,}"
    )
    print(
        f"Distinct teams: {matches['home_team'].n_unique()} home, {matches['away_team'].n_unique()} away"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
