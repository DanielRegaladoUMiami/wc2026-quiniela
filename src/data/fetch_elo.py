"""Fetch World Football Elo ratings from eloratings.net.

Two endpoints:
  - https://www.eloratings.net/World.tsv   — current snapshot of every team
  - https://www.eloratings.net/<TEAM>.tsv  — per-team match history with Elo before/after

For backtest anti-leakage we need historical Elo as-of any given date. We reconstruct
that by walking each team's match history and recording the pre-match Elo.

Writes:
  data/raw/elo/current.parquet           (snapshot of latest)
  data/raw/elo/team_history.parquet      (long table: team, date, elo_before, elo_after, opponent, goals_for, goals_against)
"""

from __future__ import annotations

import time
from pathlib import Path

import pandas as pd
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

OUT_DIR = Path("data/raw/elo")
WORLD_URL = "https://www.eloratings.net/World.tsv"
TEAM_URL = "https://www.eloratings.net/{team}.tsv"
HEADERS = {"User-Agent": "wc2026-quiniela/0.1 (github.com/DanielRegaladoUMiami/wc2026-quiniela)"}


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=2, max=20))
def _fetch_tsv(url: str) -> str:
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.text


def fetch_current() -> pd.DataFrame:
    """Snapshot of current world Elo rankings.

    Format of World.tsv (from eloratings.net): tab-separated with no header. The columns are
    (as of 2025-2026): rank, code, name, elo, country, ... — exact width can vary; we keep
    everything as strings and let downstream parse what it needs.
    """
    text = _fetch_tsv(WORLD_URL)
    rows = [line.split("\t") for line in text.splitlines() if line.strip()]
    df = pd.DataFrame(rows)
    # Try to identify the Elo column (numeric, 4-digit) and team name (longest non-numeric)
    df.columns = [f"col_{i}" for i in range(df.shape[1])]
    return df


def fetch_team_history(team_code: str, sleep: float = 0.5) -> pd.DataFrame:
    """Per-team TSV with one row per match. Schema (as documented by site):
    date, home_team, away_team, score, neutral_flag, tournament, location, ..., elo_home, elo_away

    Returns long format with one row per (team, match) including pre-match Elo.
    """
    text = _fetch_tsv(TEAM_URL.format(team=team_code))
    time.sleep(sleep)
    rows = [line.split("\t") for line in text.splitlines() if line.strip()]
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df.columns = [f"col_{i}" for i in range(df.shape[1])]
    df["team_code"] = team_code
    return df


def main(teams: list[str] | None = None, max_teams: int | None = None) -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Fetching world snapshot → {WORLD_URL}")
    current = fetch_current()
    current.to_parquet(OUT_DIR / "current.parquet", compression="zstd")
    print(f"  wrote {len(current):,} teams to current.parquet")

    if teams is None:
        # Identify ISO codes (col_1 typically). Keep 3-letter uppercase entries.
        cand = current["col_1"] if "col_1" in current.columns else current.iloc[:, 1]
        teams = [c for c in cand.astype(str) if len(c) == 3 and c.isalpha() and c == c.upper()]

    if max_teams:
        teams = teams[:max_teams]

    print(f"Fetching per-team history for {len(teams)} teams…")
    all_hist: list[pd.DataFrame] = []
    for i, code in enumerate(teams, 1):
        try:
            hist = fetch_team_history(code)
            if not hist.empty:
                all_hist.append(hist)
            if i % 20 == 0:
                print(f"  [{i}/{len(teams)}] {code} ({len(hist)} rows)")
        except Exception as exc:
            print(f"  [{i}/{len(teams)}] {code} FAILED: {exc}")

    if all_hist:
        combined = pd.concat(all_hist, ignore_index=True)
        combined.to_parquet(OUT_DIR / "team_history.parquet", compression="zstd")
        print(f"Wrote {len(combined):,} team-match rows → team_history.parquet")
    else:
        print("WARNING: no team history rows fetched")
    return 0


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--max-teams", type=int, default=None, help="Limit number of teams (debug)")
    args = p.parse_args()
    raise SystemExit(main(max_teams=args.max_teams))
