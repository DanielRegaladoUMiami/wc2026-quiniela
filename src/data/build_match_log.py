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
from pathlib import Path

import polars as pl

KAGGLE_RESULTS = Path("data/raw/matches/kaggle_martj42/results.csv")
OUT = Path("data/processed/matches.parquet")

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
    df = pl.read_csv(KAGGLE_RESULTS, try_parse_dates=True)
    return (
        df.rename(
            {
                "home_team": "home_team",
                "away_team": "away_team",
                "home_score": "home_goals",
                "away_score": "away_goals",
                "tournament": "competition",
                "city": "venue_city",
                "country": "venue_country",
                "neutral": "neutral_venue",
            }
        )
        .with_columns(
            pl.col("date").cast(pl.Date).cast(pl.Utf8).alias("date_str"),
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
    matches = build()
    matches.write_parquet(OUT, compression="zstd")
    print(f"Wrote {len(matches):,} matches → {OUT}")
    print(f"Date range: {matches['date'].min()} → {matches['date'].max()}")
    print(f"Distinct teams: {matches['home_team'].n_unique()} home, {matches['away_team'].n_unique()} away")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
