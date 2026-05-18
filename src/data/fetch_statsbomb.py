"""Fetch StatsBomb Open Data for backtest tournaments and aggregate to match-level xG.

Coverage:
  - WC 2018 (competition_id=43, season_id=3)
  - WC 2022 (competition_id=43, season_id=106)
  - Euro 2020 (competition_id=55, season_id=43)
  - Euro 2024 (competition_id=55, season_id=282)
  - Copa America 2024 (competition_id=223, season_id=282)

Writes:
  - data/raw/statsbomb/matches.parquet    (one row per match, with xG sums)
  - data/raw/statsbomb/events/{cid}_{sid}.parquet  (raw events, optional, for later)
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from statsbombpy import sb

OUT_DIR = Path("data/raw/statsbomb")
COMPETITIONS = [
    (43, 3, "World Cup 2018"),
    (43, 106, "World Cup 2022"),
    (55, 43, "Euro 2020"),
    (55, 282, "Euro 2024"),
    (223, 282, "Copa America 2024"),
]


def _shots_for_matches(match_ids: list[int]) -> pd.DataFrame:
    """Return shot events with xG for a list of match_ids (iterates per match)."""
    frames: list[pd.DataFrame] = []
    for mid in match_ids:
        try:
            ev = sb.events(match_id=int(mid))
        except Exception as exc:
            print(f"    match {mid} events failed: {exc}")
            continue
        if ev is None or ev.empty:
            continue
        shots = ev[ev["type"] == "Shot"]
        if not shots.empty:
            frames.append(shots[["match_id", "team", "player", "shot_statsbomb_xg"]].copy())
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def _aggregate_xg(matches: pd.DataFrame, shots: pd.DataFrame) -> pd.DataFrame:
    """Sum xG per team per match and merge onto matches frame."""
    if shots.empty:
        matches["home_xg"] = None
        matches["away_xg"] = None
        return matches
    grouped = shots.groupby(["match_id", "team"])["shot_statsbomb_xg"].sum().reset_index(name="xg")
    out = matches.merge(
        grouped.rename(columns={"team": "home_team", "xg": "home_xg"}),
        on=["match_id", "home_team"],
        how="left",
    ).merge(
        grouped.rename(columns={"team": "away_team", "xg": "away_xg"}),
        on=["match_id", "away_team"],
        how="left",
    )
    return out


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "events").mkdir(exist_ok=True)
    all_matches: list[pd.DataFrame] = []

    for cid, sid, name in COMPETITIONS:
        print(f"\n=== {name} (cid={cid}, sid={sid}) ===")
        try:
            matches = sb.matches(competition_id=cid, season_id=sid)
        except Exception as exc:
            print(f"  matches fetch failed: {exc}")
            continue
        print(f"  matches: {len(matches)}")
        if matches.empty:
            continue
        shots = _shots_for_matches(matches["match_id"].tolist())
        print(f"  shots: {len(shots)}")
        if not shots.empty:
            shots.to_parquet(OUT_DIR / "events" / f"{cid}_{sid}_shots.parquet", compression="zstd")
        matches = _aggregate_xg(matches, shots)
        matches["competition_label"] = name
        matches["statsbomb_competition_id"] = cid
        matches["statsbomb_season_id"] = sid
        all_matches.append(matches)

    if not all_matches:
        print("No matches downloaded.")
        return 1

    combined = pd.concat(all_matches, ignore_index=True)
    combined.to_parquet(OUT_DIR / "matches.parquet", compression="zstd")
    print(f"\nWrote {len(combined):,} matches → {OUT_DIR / 'matches.parquet'}")
    print(f"Coverage with xG: {combined['home_xg'].notna().sum()} / {len(combined)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
