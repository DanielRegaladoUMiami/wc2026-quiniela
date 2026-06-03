"""Aggregate per-team metrics from processed/players.parquet + Wikipedia manager lookup.

Outputs data/processed/team_stats.parquet joined with team_metadata.
"""

from __future__ import annotations

import re
import time
from pathlib import Path

import bs4
import pandas as pd
import requests

PLAYERS = Path("data/processed/players.parquet")
META = Path("data/fixtures/team_metadata.parquet")
OUT = Path("data/processed/team_stats.parquet")
UA = "wc2026-quiniela/0.1 dxr1491@miami.edu"

TOP5_LEAGUES_CLUBS_HINT = re.compile(
    # Common substrings of Big-5 clubs (cheap heuristic — no club->league map needed)
    r"(Manchester|Liverpool|Arsenal|Chelsea|Tottenham|Newcastle|Aston Villa|West Ham|Brighton|"
    r"Crystal Palace|Everton|Fulham|Brentford|Wolves|Nottingham|Bournemouth|Leicester|"
    r"Real Madrid|Barcelona|Atl[ée]tico Madrid|Sevilla|Valencia|Villarreal|Real Sociedad|"
    r"Athletic Bilbao|Real Betis|Getafe|Osasuna|Girona|Celta|Mallorca|Las Palmas|Cadiz|"
    r"Bayern|Dortmund|Leipzig|Leverkusen|Wolfsburg|Frankfurt|Hoffenheim|Mönchengladbach|"
    r"Stuttgart|Freiburg|Union Berlin|Hertha|Werder|Mainz|Augsburg|Bochum|"
    r"Juventus|Inter|Milan|Napoli|Roma|Lazio|Fiorentina|Atalanta|Bologna|Torino|Udinese|"
    r"PSG|Paris Saint|Marseille|Lyon|Monaco|Lille|Rennes|Nice|Nantes|Strasbourg|Lens|Reims)",
    re.I,
)


def _wiki_get(title: str) -> bs4.BeautifulSoup | None:
    url = f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=20)
        if r.status_code != 200:
            return None
        return bs4.BeautifulSoup(r.text, "lxml")
    except Exception:
        return None


def fetch_manager(team: str) -> tuple[str, str]:
    """Return (manager_name, appointment_date_iso) from the team's wiki infobox."""
    for title in (f"{team} national football team", f"{team} national soccer team"):
        soup = _wiki_get(title)
        if not soup:
            continue
        info = soup.find("table", class_=re.compile("infobox"))
        if not info:
            continue
        for tr in info.find_all("tr"):
            th = tr.find("th")
            td = tr.find("td")
            if not th or not td:
                continue
            lbl = th.get_text(" ", strip=True).lower()
            if lbl in {"head coach", "manager", "coach", "head coach(es)"}:
                name = td.get_text(" ", strip=True)
                # Trim parenthetical
                name = re.sub(r"\(.*?\)", "", name)
                name = re.sub(r"\[[^\]]*\]", "", name).strip()
                return name, ""
    return "", ""


def main() -> Path:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    players = pd.read_parquet(PLAYERS)
    meta = pd.read_parquet(META)

    g = players.groupby("team", dropna=False)
    rows = []
    for team, sub in g:
        ages = pd.to_numeric(sub["age"], errors="coerce")
        mv = pd.to_numeric(sub["market_value_eur"], errors="coerce")
        in_top5 = (
            sub["club"]
            .fillna("")
            .str.contains(TOP5_LEAGUES_CLUBS_HINT.pattern, regex=True, flags=re.I)
        )
        top11_mv = mv.sort_values(ascending=False).head(11).sum() if mv.notna().any() else 0.0
        rows.append(
            {
                "team": team,
                "n_players": len(sub),
                "avg_age": float(ages.mean()) if ages.notna().any() else float("nan"),
                "median_age": float(ages.median()) if ages.notna().any() else float("nan"),
                "squad_market_value_eur_total": float(mv.sum()) if mv.notna().any() else 0.0,
                "squad_market_value_top11": float(top11_mv),
                "n_top5_league_players": int(in_top5.sum()),
            }
        )
    stats = pd.DataFrame(rows)

    # Managers
    mgr_rows = []
    for t in stats["team"]:
        name, appt = fetch_manager(t)
        mgr_rows.append({"team": t, "manager_name": name, "manager_appointed": appt})
        print(f"  mgr {t}: {name!r}")
        time.sleep(0.4)
    mgrs = pd.DataFrame(mgr_rows)
    mgrs["manager_tenure_days"] = pd.NA  # appointment-date parsing left as TODO

    out = stats.merge(mgrs, on="team", how="left").merge(meta, on="team", how="left")
    out.to_parquet(OUT, index=False)
    print(f"wrote {OUT} ({len(out)} teams)")
    return OUT


if __name__ == "__main__":
    main()
