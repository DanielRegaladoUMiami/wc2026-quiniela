"""Fetch 1X2 match odds from ESPN's free, public API (no key required).

ESPN exposes per-match moneyline odds (home / draw / away) with both an `open` and a
`close` price from DraftKings. The `close` price is the closing line — the gold standard
a sharp shop grades itself against (closing-line value). We de-vig it (Shin) into honest
probabilities.

Primary output:
  - current WC2026 group-stage matches -> data/processed/market_odds_wc2026.parquet

Note on history: ESPN's scoreboard only serves odds for live/upcoming matches; the odds
block comes back empty for past events, so a free historical-odds backtest isn't possible
here. Closing-line value (CLV) is therefore measured *live* during the tournament — each
day we snapshot the closing line and compare it to the model's earlier prediction — which
is the purest form of CLV anyway. `--history` is kept for the record but will report no
coverage until a historical-odds source is wired.

Run:
    python -m src.data.fetch_espn_odds --wc2026
"""

from __future__ import annotations

import argparse
import time
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import requests

from src.data.devig import american_to_decimal, shin_devig, vig_pct

SCOREBOARD = "https://site.api.espn.com/apis/site/v2/sports/soccer/{league}/scoreboard"
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) wc2026-quiniela/0.1"}
SOURCE = "espn_draftkings"
DELAY_S = 0.4

WC_DIR = Path("data/processed/market_odds_wc2026.parquet")
HIST_PATH = Path("data/processed/market_odds_history.parquet")

# Current WC2026 group stage (knockout matchups are TBD, so no odds exist for them yet).
WC2026_LEAGUE = "fifa.world"
WC2026_START = date(2026, 6, 11)
WC2026_END = date(2026, 6, 27)

# Past tournaments for the CLV backtest: tournament key -> (espn league slug, start, end).
HIST_TOURNAMENTS: dict[str, tuple[str, date, date]] = {
    "WC18": ("fifa.world", date(2018, 6, 14), date(2018, 7, 15)),
    "WC22": ("fifa.world", date(2022, 11, 20), date(2022, 12, 18)),
    "Euro20": ("uefa.euro", date(2021, 6, 11), date(2021, 7, 11)),
    "Euro24": ("uefa.euro", date(2024, 6, 14), date(2024, 7, 14)),
    "Copa24": ("conmebol.america", date(2024, 6, 20), date(2024, 7, 14)),
}

# ESPN display name -> our canonical team name (only where they differ).
NAME_ALIASES = {
    "Czech Republic": "Czechia",
    "Korea Republic": "South Korea",
    "IR Iran": "Iran",
    "Türkiye": "Turkey",
    "Turkiye": "Turkey",
    "Côte d'Ivoire": "Ivory Coast",
    "Cote d'Ivoire": "Ivory Coast",
    "USA": "United States",
    "Bosnia & Herzegovina": "Bosnia-Herzegovina",
}


@dataclass
class OddsRow:
    date: str
    home_team: str
    away_team: str
    odds_home: float
    odds_draw: float
    odds_away: float
    p_home_market: float
    p_draw_market: float
    p_away_market: float
    source: str
    tournament: str
    vig_pct: float


def _canon(name: str | None) -> str | None:
    if not name:
        return name
    return NAME_ALIASES.get(name, name)


def _price(side: dict | None) -> float | None:
    """Pull the close (else open) American odds from a moneyline side block."""
    if not side:
        return None
    for key in ("close", "open"):
        leg = side.get(key)
        if leg and leg.get("odds") not in (None, ""):
            try:
                return american_to_decimal(leg["odds"])
            except (ValueError, TypeError):
                return None
    return None


def _parse_event(ev: dict, tournament: str) -> OddsRow | None:
    comp = (ev.get("competitions") or [{}])[0]
    teams = {
        c.get("homeAway"): c.get("team", {}).get("displayName") for c in comp.get("competitors", [])
    }
    home, away = _canon(teams.get("home")), _canon(teams.get("away"))
    odds_list = comp.get("odds") or []
    if not (home and away and odds_list):
        return None
    ml = (odds_list[0] or {}).get("moneyline") or {}
    o_h, o_d, o_a = _price(ml.get("home")), _price(ml.get("draw")), _price(ml.get("away"))
    if None in (o_h, o_d, o_a):
        return None
    p_h, p_d, p_a = shin_devig(o_h, o_d, o_a)
    return OddsRow(
        date=str(pd.to_datetime(ev.get("date")).date()),
        home_team=home,
        away_team=away,
        odds_home=o_h,
        odds_draw=o_d,
        odds_away=o_a,
        p_home_market=p_h,
        p_draw_market=p_d,
        p_away_market=p_a,
        source=SOURCE,
        tournament=tournament,
        vig_pct=vig_pct(o_h, o_d, o_a),
    )


def fetch_window(league: str, start: date, end: date, tournament: str) -> list[OddsRow]:
    rows: list[OddsRow] = []
    d = start
    while d <= end:
        url = SCOREBOARD.format(league=league)
        try:
            r = requests.get(
                url, headers=HEADERS, params={"dates": d.strftime("%Y%m%d")}, timeout=30
            )
            r.raise_for_status()
            events = r.json().get("events", [])
        except Exception as e:
            print(f"  [{tournament} {d}] fetch failed: {e}")
            events = []
        for ev in events:
            row = _parse_event(ev, tournament)
            if row:
                rows.append(row)
        d += timedelta(days=1)
        time.sleep(DELAY_S)
    return rows


def _write(rows: list[OddsRow], path: Path) -> pd.DataFrame:
    df = pd.DataFrame([asdict(r) for r in rows]).drop_duplicates(
        subset=["date", "home_team", "away_team"], keep="last"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)
    return df


def run_wc2026() -> pd.DataFrame:
    print(f"WC2026 group-stage odds: {WC2026_START} → {WC2026_END}")
    rows = fetch_window(WC2026_LEAGUE, WC2026_START, WC2026_END, "WC2026")
    df = _write(rows, WC_DIR)
    cov = df["date"].nunique() if len(df) else 0
    print(f"  wrote {len(df)} matches across {cov} matchdays → {WC_DIR}")
    if len(df):
        print(f"  avg vig: {df['vig_pct'].mean():.1f}%")
    return df


def run_history() -> pd.DataFrame:
    all_rows: list[OddsRow] = []
    for key, (league, start, end) in HIST_TOURNAMENTS.items():
        rows = fetch_window(league, start, end, key)
        print(f"[{key}] {len(rows)} matches")
        all_rows.extend(rows)
    df = _write(all_rows, HIST_PATH)
    per = df.groupby("tournament").size().to_dict() if len(df) else {}
    print(f"wrote {len(df)} historical matches → {HIST_PATH}; coverage: {per}")
    if not len(df):
        print(
            "NOTE: ESPN does not expose odds for past matches (odds block is empty), so "
            "there is no free historical CLV backtest. CLV is measured live during the "
            "tournament instead — see the module docstring."
        )
    return df


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--wc2026", action="store_true", help="fetch current WC2026 group-stage odds")
    ap.add_argument(
        "--history", action="store_true", help="fetch past-tournament odds for CLV backtest"
    )
    args = ap.parse_args()
    if not (args.wc2026 or args.history):
        args.wc2026 = True
    if args.wc2026:
        run_wc2026()
    if args.history:
        run_history()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
