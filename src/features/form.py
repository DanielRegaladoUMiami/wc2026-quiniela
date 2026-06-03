"""Rolling form features per team.

Walks matches chronologically and emits, for each (team, match), the team's metrics over
the previous N matches (5, 10, 20):
  ppg, gf_pm, ga_pm, gd_pm, win_rate, days_since_last_match,
  ppg_vs_top20, gd_pm_vs_top20

`vs_top20` filters opponents to those with Elo pre-match >= 1900 (proxy for tier).

Output: data/processed/team_form.parquet  (one row per (team, match_id))
"""

from __future__ import annotations

from collections import deque
from pathlib import Path

import pandas as pd
import polars as pl

WINDOWS = (5, 10, 20)
TOP_ELO_THRESHOLD = 1900.0


def _ppg(home_goals: int, away_goals: int) -> int:
    if home_goals > away_goals:
        return 3
    if home_goals == away_goals:
        return 1
    return 0


def compute_form(matches: pd.DataFrame, elo_pre: pd.DataFrame) -> pd.DataFrame:
    df = matches.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.dropna(subset=["home_goals", "away_goals"]).sort_values("date").reset_index(drop=True)
    df["home_goals"] = df["home_goals"].astype(int)
    df["away_goals"] = df["away_goals"].astype(int)

    elo_lookup = elo_pre.set_index("match_id")[["home_elo_pre", "away_elo_pre"]].to_dict("index")

    state: dict[str, deque] = {}  # team -> deque of (date, gf, ga, ppg, opp_elo)
    rows: list[dict] = []

    for r in df.itertuples(index=False):
        for side, team, gf, ga, opp_elo in (
            (
                "home",
                r.home_team,
                r.home_goals,
                r.away_goals,
                elo_lookup.get(r.match_id, {}).get("away_elo_pre", 1500.0),
            ),
            (
                "away",
                r.away_team,
                r.away_goals,
                r.home_goals,
                elo_lookup.get(r.match_id, {}).get("home_elo_pre", 1500.0),
            ),
        ):
            hist = state.setdefault(team, deque(maxlen=max(WINDOWS) + 5))
            row = {"match_id": r.match_id, "date": r.date, "team": team, "side": side}
            for w in WINDOWS:
                last = list(hist)[-w:]
                if last:
                    row[f"ppg_{w}"] = sum(x["ppg"] for x in last) / len(last)
                    row[f"gf_pm_{w}"] = sum(x["gf"] for x in last) / len(last)
                    row[f"ga_pm_{w}"] = sum(x["ga"] for x in last) / len(last)
                    row[f"gd_pm_{w}"] = row[f"gf_pm_{w}"] - row[f"ga_pm_{w}"]
                    row[f"win_rate_{w}"] = sum(1 for x in last if x["ppg"] == 3) / len(last)
                    strong = [x for x in last if x["opp_elo"] >= TOP_ELO_THRESHOLD]
                    if strong:
                        row[f"ppg_vs_top_{w}"] = sum(x["ppg"] for x in strong) / len(strong)
                        row[f"gd_pm_vs_top_{w}"] = sum(x["gf"] - x["ga"] for x in strong) / len(
                            strong
                        )
                    else:
                        row[f"ppg_vs_top_{w}"] = None
                        row[f"gd_pm_vs_top_{w}"] = None
                else:
                    for k in (
                        f"ppg_{w}",
                        f"gf_pm_{w}",
                        f"ga_pm_{w}",
                        f"gd_pm_{w}",
                        f"win_rate_{w}",
                        f"ppg_vs_top_{w}",
                        f"gd_pm_vs_top_{w}",
                    ):
                        row[k] = None
            row["days_since_last"] = (r.date - hist[-1]["date"]).days if hist else None
            rows.append(row)
            hist.append(
                {"date": r.date, "gf": gf, "ga": ga, "ppg": _ppg(gf, ga), "opp_elo": opp_elo}
            )

    return pd.DataFrame(rows)


def main() -> int:
    matches = pl.read_parquet("data/processed/matches.parquet").to_pandas()
    elo_pre = pl.read_parquet("data/processed/elo_pre_match.parquet").to_pandas()
    print(f"Computing form on {len(matches):,} matches…")
    form = compute_form(matches, elo_pre)
    out = Path("data/processed/team_form.parquet")
    form.to_parquet(out, compression="zstd")
    print(f"Wrote {len(form):,} (team, match) rows → {out}")
    print(form.head(3))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
