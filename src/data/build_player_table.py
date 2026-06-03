"""Unify wiki squads + FBref intl + TM market values + Wikidata photos into one
row-per-player processed table.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

WIKI = Path("data/raw/squads/wiki_squads.parquet")
FBREF = Path("data/raw/fbref/intl_player_stats.parquet")
TM = Path("data/raw/transfermarkt/squads.parquet")
PHOTOS = Path("data/raw/photos/manifest.parquet")
META = Path("data/fixtures/team_metadata.parquet")
OUT = Path("data/processed/players.parquet")


def _age(dob: str) -> float:
    if not dob or pd.isna(dob):
        return float("nan")
    try:
        y, m, d = (int(x) for x in dob.split("-"))
        today = date.today()
        return today.year - y - ((today.month, today.day) < (m, d))
    except Exception:
        return float("nan")


def main() -> Path:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    wiki = pd.read_parquet(WIKI)
    fbref = pd.read_parquet(FBREF) if FBREF.exists() else pd.DataFrame()
    tm = pd.read_parquet(TM) if TM.exists() else pd.DataFrame()
    photos = pd.read_parquet(PHOTOS) if PHOTOS.exists() else pd.DataFrame()
    meta = pd.read_parquet(META)[["team", "fifa_code"]]

    # Base from wiki, dedup
    base = wiki.drop_duplicates(subset=["team", "player_name"]).copy()
    base["age"] = base["dob"].apply(_age)

    # FBref intl stats
    if not fbref.empty:
        rename = {"player": "player_name"}
        # FBref WC2022 lacks xG; expose available columns as proxies
        for src, dst in (
            ("Performance_Gls", "intl_goals"),
            ("Playing Time_Min", "intl_minutes"),
            ("Playing Time_MP", "intl_matches"),
            ("Per 90 Minutes_Gls", "intl_goals_per_90"),
        ):
            if src in fbref.columns:
                rename[src] = dst
        fb = fbref.rename(columns=rename)
        fb["intl_xg"] = pd.NA  # not provided by FBref tournament endpoint
        keep = ["team", "player_name", "intl_xg"]
        for c in ("intl_goals", "intl_minutes", "intl_matches", "intl_goals_per_90"):
            if c in fb.columns:
                keep.append(c)
        fb = fb[keep].drop_duplicates(subset=["team", "player_name"])
        if {"intl_goals", "intl_matches"}.issubset(fb.columns):
            mp = pd.to_numeric(fb["intl_matches"], errors="coerce")
            gls = pd.to_numeric(fb["intl_goals"], errors="coerce")
            fb["intl_goals_per_match"] = (gls / mp).where(mp > 0)
        base = base.merge(fb, on=["team", "player_name"], how="left")

    # TM market values
    if not tm.empty:
        tcols = ["team", "player_name", "market_value_eur", "contract_until"]
        tcols = [c for c in tcols if c in tm.columns]
        base = base.merge(
            tm[tcols].drop_duplicates(subset=["team", "player_name"]),
            on=["team", "player_name"],
            how="left",
        )
    if "market_value_eur" not in base.columns:
        base["market_value_eur"] = pd.NA
    if "contract_until" not in base.columns:
        base["contract_until"] = pd.NA

    # Photos
    if not photos.empty:
        base = base.merge(
            photos[["team", "player_name", "image_url"]].rename(columns={"image_url": "photo_url"}),
            on=["team", "player_name"],
            how="left",
        )
    else:
        base["photo_url"] = ""

    base = base.merge(meta, on="team", how="left")

    cols = [
        "team",
        "fifa_code",
        "player_name",
        "position",
        "age",
        "dob",
        "club",
        "caps",
        "goals",
        "intl_xg",
        "intl_goals_per_match",
        "market_value_eur",
        "contract_until",
        "photo_url",
        "shirt_number",
    ]
    for c in cols:
        if c not in base.columns:
            base[c] = pd.NA
    out = base[cols].copy()
    out.to_parquet(OUT, index=False)
    print(f"wrote {OUT} ({len(out)} players, {out['team'].nunique()} teams)")
    return OUT


if __name__ == "__main__":
    main()
