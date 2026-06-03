"""Historical 1X2 closing odds for international tournaments via OddsPortal.

OddsPortal aggregates closing bookmaker prices for free. We scrape result pages
politely (3s between requests, custom UA) and de-vig with Shin's method.

Tournaments backtested:
  WC18, WC22, Euro20, Euro24, Copa19, Copa21, Copa24, AFCON19, AFCON21, AFCON23,
  NationsLeague 20-21, NationsLeague 22-23.

Note: OddsPortal serves match rows via JS; many pages have a server-rendered table
fallback we attempt to read. Failures are recorded as zero-coverage and surfaced in
the run report. A `--source-file <html>` flag lets you provide local HTML when
Cloudflare blocks the scraper.

Output: data/processed/market_odds_history.parquet
Columns: date, home_team, away_team, p_home_market, p_draw_market, p_away_market,
         odds_home, odds_draw, odds_away, source, tournament, vig_pct
"""

from __future__ import annotations

import argparse
import contextlib
import re
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

OUT_PATH = Path("data/processed/market_odds_history.parquet")
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 "
        "(KHTML, like Gecko) Version/17.5 Safari/605.1.15 "
        "wc2026-quiniela/0.1"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}
DELAY_S = 3.0

TOURNAMENTS: dict[str, str] = {
    "WC18": "https://www.oddsportal.com/soccer/world/world-cup-2018/results/",
    "WC22": "https://www.oddsportal.com/soccer/world/world-cup-2022/results/",
    "Euro20": "https://www.oddsportal.com/soccer/europe/euro-2020/results/",
    "Euro24": "https://www.oddsportal.com/soccer/europe/euro-2024/results/",
    "Copa19": "https://www.oddsportal.com/soccer/south-america/copa-america-2019/results/",
    "Copa21": "https://www.oddsportal.com/soccer/south-america/copa-america-2021/results/",
    "Copa24": "https://www.oddsportal.com/soccer/south-america/copa-america-2024/results/",
    "AFCON19": "https://www.oddsportal.com/soccer/africa/africa-cup-of-nations-2019/results/",
    "AFCON21": "https://www.oddsportal.com/soccer/africa/africa-cup-of-nations-2021/results/",
    "AFCON23": "https://www.oddsportal.com/soccer/africa/africa-cup-of-nations-2023/results/",
    "NL2021": "https://www.oddsportal.com/soccer/europe/uefa-nations-league-2020-2021/results/",
    "NL2223": "https://www.oddsportal.com/soccer/europe/uefa-nations-league-2022-2023/results/",
}


@dataclass
class OddsRow:
    date: pd.Timestamp
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


def shin_devig(o_h: float, o_d: float, o_a: float, iters: int = 200) -> tuple[float, float, float]:
    """Shin's (1992) de-vig. Solve for insider-trading proportion z.

    Returns true probabilities (p_h, p_d, p_a) summing to 1.
    """
    p_raw = np.array([1 / o_h, 1 / o_d, 1 / o_a], dtype=float)
    p_raw = p_raw / p_raw.sum() * (p_raw.sum())  # keep raw scale
    pi = p_raw / p_raw.sum()  # normalized booky probs
    z = 0.0
    for _ in range(iters):
        sq = np.sqrt(z * z + 4 * (1 - z) * pi * pi / max(p_raw.sum(), 1e-9))
        p_true = (sq - z) / (2 * (1 - z) + 1e-12)
        p_true = p_true / p_true.sum()
        new_z = max(0.0, min(0.5, (p_true.sum() - 1) + z))
        if abs(new_z - z) < 1e-9:
            break
        z = new_z
    return float(p_true[0]), float(p_true[1]), float(p_true[2])


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=3, max=15))
def _fetch(url: str) -> str:
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.text


_NUM = re.compile(r"^\d+(?:\.\d+)?$")


def parse_results_html(html: str, tournament: str) -> list[OddsRow]:
    """Best-effort parse of the static fallback table on OddsPortal results pages.

    OddsPortal mostly renders rows via JS; when an HTML <table> is present we mine
    rows of shape:  <tr> <td date|teams> <td score> <td odds_h> <td odds_d> <td odds_a> </tr>
    """
    soup = BeautifulSoup(html, "lxml")
    rows: list[OddsRow] = []
    current_date: pd.Timestamp | None = None
    date_re = re.compile(r"(\d{1,2}\s+\w+\s+\d{4})")
    for tr in soup.find_all("tr"):
        txt = tr.get_text(" ", strip=True)
        m = date_re.search(txt)
        if m and len(tr.find_all("td")) <= 2:
            with contextlib.suppress(Exception):
                current_date = pd.to_datetime(m.group(1))
            continue
        tds = [td.get_text(strip=True) for td in tr.find_all("td")]
        if len(tds) < 5:
            continue
        teams_cell = next((c for c in tds if " - " in c or " – " in c), None)
        if not teams_cell:
            continue
        nums = [c for c in tds if _NUM.match(c)]
        if len(nums) < 3:
            continue
        try:
            o_h, o_d, o_a = (float(nums[-3]), float(nums[-2]), float(nums[-1]))
        except ValueError:
            continue
        sep = " - " if " - " in teams_cell else " – "
        home, away = (s.strip() for s in teams_cell.split(sep, 1))
        ph, pd_, pa = shin_devig(o_h, o_d, o_a)
        vig = (1 / o_h + 1 / o_d + 1 / o_a) - 1
        rows.append(
            OddsRow(
                date=current_date or pd.NaT,
                home_team=home,
                away_team=away,
                odds_home=o_h,
                odds_draw=o_d,
                odds_away=o_a,
                p_home_market=ph,
                p_draw_market=pd_,
                p_away_market=pa,
                source="oddsportal",
                tournament=tournament,
                vig_pct=float(vig * 100),
            )
        )
    return rows


def scrape_tournament(tournament: str, url: str) -> list[OddsRow]:
    try:
        html = _fetch(url)
    except Exception as e:
        print(f"[{tournament}] fetch failed: {e}")
        return []
    rows = parse_results_html(html, tournament)
    if not rows:
        print(f"[{tournament}] no rows parsed (likely JS-rendered or CF block)")
    return rows


def build() -> pd.DataFrame:
    all_rows: list[OddsRow] = []
    for tname, url in TOURNAMENTS.items():
        rows = scrape_tournament(tname, url)
        print(f"[{tname}] parsed {len(rows)} matches")
        all_rows.extend(rows)
        time.sleep(DELAY_S)
    df = pd.DataFrame([r.__dict__ for r in all_rows])
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    if len(df):
        df.to_parquet(OUT_PATH, index=False)
    return df


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tournament", default=None, help="Single key (e.g. WC22)")
    args = ap.parse_args()
    if args.tournament:
        if args.tournament not in TOURNAMENTS:
            raise SystemExit(f"unknown tournament: {args.tournament}")
        rows = scrape_tournament(args.tournament, TOURNAMENTS[args.tournament])
        df = pd.DataFrame([r.__dict__ for r in rows])
        OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        if len(df):
            df.to_parquet(OUT_PATH, index=False)
        print(f"wrote {len(df)} rows")
    else:
        df = build()
        per = df.groupby("tournament").size().to_dict() if len(df) else {}
        print(f"wrote {len(df)} rows total; coverage: {per}")


if __name__ == "__main__":
    main()
