#!/usr/bin/env python3
"""Convert parquet data files to JSON for static consumption by the Next.js site.

Runs as a `prebuild` step from package.json.
"""
import json
import os
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SIM_DIR = ROOT / "data" / "sims" / "sim_run_202605190049"
FIX_DIR = ROOT / "data" / "fixtures"
OUT = Path(__file__).resolve().parents[1] / "public" / "data"
OUT.mkdir(parents=True, exist_ok=True)


def df_to_json(df: pd.DataFrame, path: Path) -> None:
    # Convert dates / timestamps to ISO strings.
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.strftime("%Y-%m-%d")
        elif df[col].dtype == "object":
            # Convert python date objects
            df[col] = df[col].map(lambda x: x.isoformat() if hasattr(x, "isoformat") else x)
    records = json.loads(df.to_json(orient="records"))
    path.write_text(json.dumps(records, separators=(",", ":")))
    print(f"  -> {path.relative_to(ROOT)} ({len(records)} rows, {path.stat().st_size//1024}KB)")


def main() -> None:
    print("Converting parquet -> JSON ...")

    teams = pd.read_parquet(FIX_DIR / "team_metadata.parquet")
    fixtures = pd.read_parquet(FIX_DIR / "wc2026_fixtures.parquet")
    venues = pd.read_parquet(FIX_DIR / "venues.parquet")
    groups = pd.read_parquet(FIX_DIR / "groups.parquet")
    adv = pd.read_parquet(SIM_DIR / "advancement.parquet")
    mp = pd.read_parquet(SIM_DIR / "match_probs.parquet")

    # Join group label onto teams
    teams = teams.merge(groups, left_on="team", right_on="team", how="left")

    # Join champion prob into teams
    teams = teams.merge(adv[["team", "p_champion", "p_advance_group"]], on="team", how="left")

    # Build per-team fixtures map
    df_to_json(teams, OUT / "teams.json")
    df_to_json(fixtures, OUT / "fixtures.json")
    df_to_json(venues, OUT / "venues.json")
    df_to_json(groups, OUT / "groups.json")
    df_to_json(adv, OUT / "advancement.json")
    df_to_json(mp, OUT / "match_probs.json")

    # Backtest files
    try:
        bt_wc = pd.read_parquet(ROOT / "data" / "sims" / "backtest_gbm_wc2022.parquet")
        df_to_json(bt_wc, OUT / "backtest_wc2022.json")
    except Exception as e:  # noqa
        print(f"  (skip wc backtest: {e})")
    try:
        bt_eu = pd.read_parquet(ROOT / "data" / "sims" / "backtest_gbm_euro2024.parquet")
        df_to_json(bt_eu, OUT / "backtest_euro2024.json")
    except Exception as e:  # noqa
        print(f"  (skip euro backtest: {e})")

    # Sample brackets — aggregated round occupancy for /bracket page.
    sb = pd.read_parquet(SIM_DIR / "sample_brackets.parquet")
    # Per round (stage), how often each team appears
    occupancy = (
        sb.groupby(["stage", "home"]).size().rename("n").reset_index()
    )
    occupancy2 = (
        sb.groupby(["stage", "away"]).size().rename("n").reset_index().rename(columns={"away": "home"})
    )
    occ = pd.concat([occupancy, occupancy2], ignore_index=True).groupby(["stage", "home"], as_index=False)["n"].sum()
    n_sims = sb["sim_id"].nunique()
    occ["pct"] = occ["n"] / n_sims
    occ = occ.rename(columns={"home": "team"})
    df_to_json(occ, OUT / "round_occupancy.json")

    # Edge board: pure-model vs de-vigged market for the live WC2026 slate.
    try:
        edge = pd.read_parquet(ROOT / "data" / "processed" / "edge_wc2026.parquet")
        codes = teams[["team", "iso2", "fifa_code", "conf"]].drop_duplicates("team")
        edge = edge.merge(
            codes.rename(
                columns={"team": "home_team", "iso2": "home_iso2", "fifa_code": "home_code", "conf": "home_conf"}
            ),
            on="home_team",
            how="left",
        ).merge(
            codes.rename(
                columns={"team": "away_team", "iso2": "away_iso2", "fifa_code": "away_code", "conf": "away_conf"}
            ),
            on="away_team",
            how="left",
        )
        edge = edge.sort_values("best_edge_pts", ascending=False)
        df_to_json(edge, OUT / "edge.json")
    except Exception as e:  # noqa
        print(f"  (skip edge: {e})")

    meta = {
        "sim_run": "sim_run_202605190049",
        "n_sims": int(n_sims),
        "n_matches": int(len(fixtures)),
        "n_teams": int(len(teams)),
        "kickoff_iso": "2026-06-11T17:00:00-05:00",
        "generated_at": pd.Timestamp.utcnow().isoformat(),
    }
    (OUT / "meta.json").write_text(json.dumps(meta))
    print(f"  -> meta.json")
    print("Done.")


if __name__ == "__main__":
    main()
