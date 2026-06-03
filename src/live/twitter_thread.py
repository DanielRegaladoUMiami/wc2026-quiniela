"""Generate a daily/post-match Twitter/X thread of model picks.

Read-only generator: produces a markdown-flavored thread that can be posted manually
or via a GitHub Action with TWITTER_API_TOKEN (currently outputs to stdout / file).

Format:
  1/ 🌍 World Cup 2026 — today's picks (DD MMM)
  2/ Champion top-5 (with deltas vs. yesterday if cached)
  3/ Today's matches: 🇪🇸 Spain vs 🇨🇻 Cape Verde — model 82%/13%/5% | Recommended 1X2: HOME
  4/ Contrarian alert: 🇲🇦 Morocco vs 🇧🇷 Brazil — model 34% Morocco vs Kalshi 18%
  5/ Methodology + repo links
"""

from __future__ import annotations

import argparse
from datetime import date as Date
from pathlib import Path

import pandas as pd
import polars as pl

from src.sims.bracket_2026 import all_fixtures_df

FLAG_EMOJI = {
    "MX": "🇲🇽",
    "ZA": "🇿🇦",
    "KR": "🇰🇷",
    "CZ": "🇨🇿",
    "CA": "🇨🇦",
    "BA": "🇧🇦",
    "QA": "🇶🇦",
    "CH": "🇨🇭",
    "BR": "🇧🇷",
    "MA": "🇲🇦",
    "HT": "🇭🇹",
    "GB-SCT": "🏴󠁧󠁢󠁳󠁣󠁴󠁿",
    "US": "🇺🇸",
    "PY": "🇵🇾",
    "AU": "🇦🇺",
    "TR": "🇹🇷",
    "DE": "🇩🇪",
    "CW": "🇨🇼",
    "CI": "🇨🇮",
    "EC": "🇪🇨",
    "NL": "🇳🇱",
    "JP": "🇯🇵",
    "SE": "🇸🇪",
    "TN": "🇹🇳",
    "BE": "🇧🇪",
    "EG": "🇪🇬",
    "IR": "🇮🇷",
    "NZ": "🇳🇿",
    "ES": "🇪🇸",
    "CV": "🇨🇻",
    "SA": "🇸🇦",
    "UY": "🇺🇾",
    "FR": "🇫🇷",
    "SN": "🇸🇳",
    "IQ": "🇮🇶",
    "NO": "🇳🇴",
    "AR": "🇦🇷",
    "DZ": "🇩🇿",
    "AT": "🇦🇹",
    "JO": "🇯🇴",
    "PT": "🇵🇹",
    "CD": "🇨🇩",
    "UZ": "🇺🇿",
    "CO": "🇨🇴",
    "GB-ENG": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    "HR": "🇭🇷",
    "GH": "🇬🇭",
    "PA": "🇵🇦",
}


def _latest_sim_dir() -> Path | None:
    runs = sorted(Path("data/sims").glob("sim_run_*"))
    return runs[-1] if runs else None


def _flag(team: str, meta: pd.DataFrame) -> str:
    row = meta[meta["team"] == team]
    if row.empty:
        return "🏳️"
    return FLAG_EMOJI.get(row.iloc[0]["iso2"], "🏳️")


def build_thread(target_date: Date) -> list[str]:
    meta = pl.read_parquet("data/fixtures/team_metadata.parquet").to_pandas()
    fixtures = all_fixtures_df()
    fixtures["date"] = pd.to_datetime(fixtures["date"]).dt.date
    sim_dir = _latest_sim_dir()
    if sim_dir is None:
        return ["⚠️ Predictions not yet generated. Run `make sim`."]

    adv = pl.read_parquet(sim_dir / "advancement.parquet").to_pandas()
    match_probs = pl.read_parquet(sim_dir / "match_probs.parquet").to_pandas()

    tweets: list[str] = []
    tweets.append(
        f"🌍 World Cup 2026 — picks for {target_date.strftime('%a %d %b %Y')}\n\n"
        f"Probabilistic ensemble (Dixon-Coles + Hierarchical Bayesian + LightGBM).\n"
        f"Full model: https://github.com/DanielRegaladoUMiami/wc2026-quiniela 🧵👇"
    )

    top5 = adv.sort_values("p_champion", ascending=False).head(5).reset_index(drop=True)
    lines = ["🏆 Champion top 5:"]
    for _, r in top5.iterrows():
        lines.append(f"  {_flag(r['team'], meta)} {r['team']}: {r['p_champion'] * 100:.1f}%")
    tweets.append("\n".join(lines))

    today_matches = fixtures[fixtures["date"] == target_date]
    if not today_matches.empty:
        lines = [f"⚽ Today's matches ({len(today_matches)}):"]
        mp_by_num = (
            {int(r["match_num"]): r for _, r in match_probs.iterrows()}
            if "match_num" in match_probs.columns
            else {}
        )
        for _, m in today_matches.iterrows():
            home = m.get("home")
            away = m.get("away")
            if pd.isna(home) or pd.isna(away):
                continue
            mp = mp_by_num.get(int(m["num"]))
            if mp is not None:
                ph = mp.get("p_home_win", 0.0)
                pd_ = mp.get("p_draw", 0.0)
                pa = mp.get("p_away_win", 0.0)
                pick = "HOME" if ph > max(pd_, pa) else ("DRAW" if pd_ > pa else "AWAY")
                lines.append(
                    f"  {_flag(home, meta)} {home} vs {_flag(away, meta)} {away}: {ph * 100:.0f}/{pd_ * 100:.0f}/{pa * 100:.0f} → {pick}"
                )
            else:
                lines.append(f"  {_flag(home, meta)} {home} vs {_flag(away, meta)} {away}")
        tweets.append("\n".join(lines))

    tweets.append(
        "📊 Full bracket + methodology:\n"
        "https://danielregaladocardoso-wc2026-quiniela.hf.space\n\n"
        "Models are wrong; some are useful. Not financial advice."
    )

    return tweets


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--date", default=Date.today().isoformat())
    p.add_argument("--out", default="-")
    args = p.parse_args()

    target = Date.fromisoformat(args.date)
    tweets = build_thread(target)
    text = "\n\n" + ("-" * 40 + "\n").join(tweets)
    if args.out == "-":
        print(text)
    else:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text)
        print(f"Thread written to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
