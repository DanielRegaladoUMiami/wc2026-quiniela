"""Custom Elo ratings computed from the unified match log.

Standard Elo with football tweaks (World Football Elo conventions):
  - Initial rating 1500
  - K depends on tournament: WC final stage 60, WC group 50, continental 45, qualifier 35, friendly 20
  - Goal-difference multiplier (Davidson) so big wins move more
  - Home advantage = +100 Elo equivalent (added to home rating before expected score)
  - Neutral venue → no home advantage

Walks matches chronologically and emits an "as-of-date" rating table, so backtests can
pull `elo_as_of(team, date)` without leakage.

Outputs (`data/processed/`):
  elo_ratings_history.parquet   long table: team, date, elo_after_match
  elo_pre_match.parquet         per-match table joinable to features: match_id, home_elo_pre, away_elo_pre
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import polars as pl

INIT_RATING = 1500.0
HOME_ADVANTAGE = 100.0


def k_factor(competition: str) -> float:
    c = (competition or "").lower()
    if "world cup" in c and any(s in c for s in ["final", "semi", "quarter", "round", "knockout"]):
        return 60.0
    if "world cup" in c:
        return 50.0
    if any(t in c for t in ["euro", "copa", "africa", "asian", "concacaf gold", "nations league"]):
        return 45.0
    if "qualif" in c or "qualifier" in c:
        return 35.0
    if "friendly" in c:
        return 20.0
    return 35.0


def goal_diff_multiplier(home_goals: int, away_goals: int) -> float:
    gd = abs(int(home_goals) - int(away_goals))
    if gd <= 1:
        return 1.0
    if gd == 2:
        return 1.5
    return (11.0 + gd) / 8.0


def expected_score(rating_a: float, rating_b: float) -> float:
    return 1.0 / (1.0 + 10.0 ** ((rating_b - rating_a) / 400.0))


def compute_elo(matches: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Walk matches chronologically, return (history, pre_match)."""
    df = matches.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.dropna(subset=["home_goals", "away_goals"]).sort_values("date").reset_index(drop=True)
    df["home_goals"] = df["home_goals"].astype(int)
    df["away_goals"] = df["away_goals"].astype(int)

    rating: dict[str, float] = {}
    history_rows: list[dict] = []
    pre_rows: list[dict] = []

    for row in df.itertuples(index=False):
        home, away = row.home_team, row.away_team
        rh = rating.get(home, INIT_RATING)
        ra = rating.get(away, INIT_RATING)

        rh_eff = rh + (0 if bool(getattr(row, "neutral_venue", False)) else HOME_ADVANTAGE)
        eh = expected_score(rh_eff, ra)
        ea = 1.0 - eh

        if row.home_goals > row.away_goals:
            sh, sa = 1.0, 0.0
        elif row.home_goals == row.away_goals:
            sh = sa = 0.5
        else:
            sh, sa = 0.0, 1.0

        k = k_factor(row.competition) * goal_diff_multiplier(row.home_goals, row.away_goals)
        new_rh = rh + k * (sh - eh)
        new_ra = ra + k * (sa - ea)

        pre_rows.append(
            {
                "match_id": row.match_id,
                "date": row.date,
                "home_team": home,
                "away_team": away,
                "home_elo_pre": rh,
                "away_elo_pre": ra,
                "home_elo_pre_with_ha": rh_eff,
                "p_home_win_elo": eh,
                "p_away_win_elo": ea,
            }
        )
        history_rows.append({"team": home, "date": row.date, "elo_after_match": new_rh})
        history_rows.append({"team": away, "date": row.date, "elo_after_match": new_ra})

        rating[home] = new_rh
        rating[away] = new_ra

    return pd.DataFrame(history_rows), pd.DataFrame(pre_rows)


def elo_as_of(history: pd.DataFrame, team: str, asof: pd.Timestamp) -> float:
    """Most recent Elo rating for `team` strictly before `asof`. Returns INIT_RATING if unknown."""
    asof = pd.Timestamp(asof)
    sub = history[(history["team"] == team) & (history["date"] < asof)]
    if sub.empty:
        return INIT_RATING
    return float(sub.sort_values("date").iloc[-1]["elo_after_match"])


def main() -> int:
    matches = pl.read_parquet("data/processed/matches.parquet").to_pandas()
    print(f"Computing Elo on {len(matches):,} matches…")
    history, pre = compute_elo(matches)
    out_dir = Path("data/processed")
    out_dir.mkdir(parents=True, exist_ok=True)
    history.to_parquet(out_dir / "elo_ratings_history.parquet", compression="zstd")
    pre.to_parquet(out_dir / "elo_pre_match.parquet", compression="zstd")

    top = (
        history.sort_values("date")
        .groupby("team")
        .tail(1)
        .sort_values("elo_after_match", ascending=False)
        .head(20)
    )
    print(f"\nWrote {len(history):,} rows → elo_ratings_history.parquet")
    print(f"Wrote {len(pre):,} rows → elo_pre_match.parquet")
    print("\nTop 20 teams by current Elo:")
    for _, r in top.iterrows():
        print(f"  {r['team']:30s}  {r['elo_after_match']:7.1f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
