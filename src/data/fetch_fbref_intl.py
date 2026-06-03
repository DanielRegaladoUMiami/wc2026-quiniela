"""Fetch national-team player stats from FBref via soccerdata.

soccerdata exposes a limited set of international competitions (INT-World Cup,
INT-European Championship). We use the 2022 World Cup as the canonical
recent-international-tournament source. Per-team data is filtered from the
all-players read.
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import pandas as pd
import soccerdata as sd

OUT = Path("data/raw/fbref/intl_player_stats.parquet")
STATE = Path("data/raw/fbref/intl_state.txt")

# FBref / soccerdata team-name mapping; WC2022 only — non-2022 teams will be absent.
WC2022 = {
    "Argentina",
    "Australia",
    "Belgium",
    "Brazil",
    "Cameroon",
    "Canada",
    "Costa Rica",
    "Croatia",
    "Denmark",
    "Ecuador",
    "England",
    "France",
    "Germany",
    "Ghana",
    "Iran",
    "Japan",
    "Mexico",
    "Morocco",
    "Netherlands",
    "Poland",
    "Portugal",
    "Qatar",
    "Saudi Arabia",
    "Senegal",
    "Serbia",
    "South Korea",
    "Spain",
    "Switzerland",
    "Tunisia",
    "United States",
    "Uruguay",
    "Wales",
}

STAT_TYPES = ["standard", "shooting", "keeper", "playing_time", "misc"]


def _load_state() -> set[str]:
    if STATE.exists():
        return {ln.strip() for ln in STATE.read_text().splitlines() if ln.strip()}
    return set()


def _save_state(done: set[str]) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text("\n".join(sorted(done)))


def fetch_player_stats(teams: list[str]) -> pd.DataFrame:
    """Pull WC2022 player stats; filter to requested teams that participated."""
    fb = sd.FBref(leagues="INT-World Cup", seasons="2022")
    frames: list[pd.DataFrame] = []
    for stype in STAT_TYPES:
        try:
            df = fb.read_player_season_stats(stat_type=stype)
            # flatten multiindex columns
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = ["_".join([str(c) for c in col if c]).strip("_") for col in df.columns]
            df = df.reset_index()
            df["_stat_type"] = stype
            frames.append(df)
            print(f"  fetched {stype}: {len(df)} rows")
        except Exception as e:
            print(f"  WARN {stype} failed: {e}")
        time.sleep(5)
    if not frames:
        return pd.DataFrame()
    # Merge by team+player; start with standard
    base = next((f for f in frames if (f["_stat_type"] == "standard").any()), frames[0])
    out = base.drop(columns=["_stat_type"])
    for f in frames:
        if f is base:
            continue
        f2 = f.drop(columns=["_stat_type"])
        merge_keys = [
            k
            for k in ("team", "player", "league", "season")
            if k in out.columns and k in f2.columns
        ]
        if not merge_keys:
            continue
        # avoid duplicate-column collisions
        dup = [c for c in f2.columns if c in out.columns and c not in merge_keys]
        f2 = f2.drop(columns=dup)
        out = out.merge(f2, on=merge_keys, how="left")
    # Filter to requested teams
    if "team" in out.columns:
        out = out[out["team"].isin(teams)].reset_index(drop=True)
    return out


def main() -> Path:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--teams", type=str, default="", help="comma-separated subset; default=all WC2026"
    )
    args = ap.parse_args()

    teams_meta = pd.read_parquet("data/fixtures/team_metadata.parquet")["team"].tolist()
    wanted = [t.strip() for t in args.teams.split(",") if t.strip()] if args.teams else teams_meta
    # only teams that participated in WC2022 will produce data
    fetchable = [t for t in wanted if t in WC2022]
    missing = [t for t in wanted if t not in WC2022]
    print(f"WC2022 fetchable: {len(fetchable)}/{len(wanted)}; missing-from-WC2022: {missing}")
    done = _load_state()
    if done and "wc2022" in done and OUT.exists():
        print(f"already complete at {OUT}; delete {STATE} to refetch")
        return OUT
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df = fetch_player_stats(fetchable)
    if df.empty:
        print("no data fetched")
        return OUT
    df.to_parquet(OUT, index=False)
    done.add("wc2022")
    _save_state(done)
    print(f"wrote {OUT} ({len(df)} rows, {df['team'].nunique() if 'team' in df else 0} teams)")
    return OUT


if __name__ == "__main__":
    main()
