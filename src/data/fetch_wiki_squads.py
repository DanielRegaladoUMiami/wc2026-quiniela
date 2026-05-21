"""Scrape Wikipedia '2026 FIFA World Cup squads' for the 26-man squads of all 48 nations.

Falls back to per-team national-team articles when the aggregate page lacks a team
(e.g. before official rosters are announced for that team).
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass
from pathlib import Path

import bs4
import pandas as pd
import requests

UA = "wc2026-quiniela/0.1 (https://github.com/DanielRegaladoUMiami/wc2026-quiniela; dxr1491@miami.edu)"
SQUADS_URL = "https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_squads"
OUT = Path("data/raw/squads/wiki_squads.parquet")

# Wiki H3 team header -> our canonical team name in team_metadata.parquet
WIKI_TO_CANON = {
    "Czech Republic": "Czechia",
    "Curaçao": "Curacao",
    "Ivory Coast": "Ivory Coast",
    "United States": "United States",
    "South Korea": "South Korea",
    "DR Congo": "DR Congo",
}

DOB_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")
POS_RE = re.compile(r"^\s*(\d+)?\s*(GK|DF|MF|FW)\s*$", re.I)


@dataclass
class Player:
    team: str
    player_name: str
    position: str
    dob: str
    club: str
    caps: float
    goals: float
    shirt_number: float
    source_url: str


def _get(url: str) -> bs4.BeautifulSoup:
    r = requests.get(url, headers={"User-Agent": UA}, timeout=30)
    r.raise_for_status()
    return bs4.BeautifulSoup(r.text, "lxml")


def _parse_pos(cell: str) -> tuple[float, str]:
    txt = cell.strip()
    m = POS_RE.match(txt)
    if m:
        n = float(m.group(1)) if m.group(1) else float("nan")
        return n, m.group(2).upper()
    parts = txt.split()
    if parts and parts[0].isdigit():
        n = float(parts[0])
        rest = " ".join(parts[1:]).strip().upper()
        return n, rest[:2] if rest else ""
    return float("nan"), txt.upper()[:2]


def _to_float(s: str) -> float:
    s = (s or "").replace(",", "").strip()
    if not s or s in {"-", "–", "—"}:
        return float("nan")
    try:
        return float(s)
    except ValueError:
        return float("nan")


def _parse_table(team: str, table: bs4.Tag, src: str) -> list[Player]:
    rows = table.find_all("tr")
    if not rows:
        return []
    header = [th.get_text(" ", strip=True).lower() for th in rows[0].find_all(["th", "td"])]
    # Identify column indices
    def idx(*names: str) -> int:
        for i, h in enumerate(header):
            for n in names:
                if n in h:
                    return i
        return -1

    i_no = idx("no.", "no", "#")
    i_pos = idx("pos")
    i_player = idx("player")
    i_dob = idx("date of birth", "birth")
    i_caps = idx("caps")
    i_goals = idx("goals")
    i_club = idx("club")
    if i_player < 0:
        return []
    out: list[Player] = []
    for tr in rows[1:]:
        cells = tr.find_all(["th", "td"])
        if len(cells) < 3:
            continue
        txts = [c.get_text(" ", strip=True) for c in cells]

        def at(i: int) -> str:
            return txts[i] if 0 <= i < len(txts) else ""

        name = at(i_player)
        if not name or len(name) < 2:
            continue
        # Filter footer/coach rows
        if name.lower().startswith(("manager", "coach", "head coach", "source")):
            continue
        pos_raw = at(i_pos)
        shirt, pos = _parse_pos(pos_raw) if pos_raw else (_to_float(at(i_no)), "")
        if i_no >= 0:
            n2 = _to_float(at(i_no))
            if not pd.isna(n2):
                shirt = n2
        dob_match = DOB_RE.search(at(i_dob))
        dob = dob_match.group(1) if dob_match else ""
        out.append(
            Player(
                team=team,
                player_name=name,
                position=pos,
                dob=dob,
                club=at(i_club),
                caps=_to_float(at(i_caps)),
                goals=_to_float(at(i_goals)),
                shirt_number=shirt,
                source_url=src,
            )
        )
    return out


def scrape_squads_page() -> list[Player]:
    soup = _get(SQUADS_URL)
    content = soup.find("div", class_="mw-parser-output")
    players: list[Player] = []
    team: str | None = None
    seen_teams: set[str] = set()
    for el in content.find_all(["h3", "table"]):
        if el.name == "h3":
            raw = el.get_text(strip=True).replace("[edit]", "")
            team = WIKI_TO_CANON.get(raw, raw)
        elif team and "wikitable" in (el.get("class") or []):
            if team in seen_teams:  # one squad table per team
                continue
            parsed = _parse_table(team, el, SQUADS_URL)
            if parsed:
                players.extend(parsed)
                seen_teams.add(team)
    return players


def scrape_team_article(team: str) -> list[Player]:
    """Fallback: per-team national football/soccer team article."""
    candidates = [
        f"{team} national football team",
        f"{team} national soccer team",
        f"{team} men's national football team",
        f"{team} men's national soccer team",
    ]
    for title in candidates:
        url = f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
        try:
            soup = _get(url)
        except Exception:
            continue
        content = soup.find("div", id="mw-content-text") or soup.find("div", class_="mw-parser-output")
        if not content:
            continue
        # Strategy 1: take squad/call-up section tables
        take = False
        for el in content.find_all(["h2", "h3", "h4", "table"]):
            if el.name in {"h2", "h3", "h4"}:
                txt = el.get_text(" ", strip=True).lower()
                take = any(k in txt for k in ("current squad", "recent call", "latest squad", "squad"))
            elif take and "wikitable" in (el.get("class") or []):
                parsed = _parse_table(team, el, url)
                if parsed:
                    return parsed
        # Strategy 2: any wikitable that looks like a squad (has Pos + Player + Caps cols)
        for tbl in content.find_all("table", class_="wikitable"):
            head = tbl.find("tr")
            if not head:
                continue
            cols = " ".join(c.get_text(" ", strip=True).lower() for c in head.find_all(["th", "td"]))
            if "player" in cols and ("caps" in cols or "club" in cols) and "pos" in cols:
                parsed = _parse_table(team, tbl, url)
                if parsed:
                    return parsed
    return []


def main() -> Path:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    teams = pd.read_parquet("data/fixtures/team_metadata.parquet")["team"].tolist()
    players = scrape_squads_page()
    covered = {p.team for p in players}
    print(f"squads-page: {len(players)} players across {len(covered)} teams")
    for t in teams:
        if t not in covered:
            time.sleep(0.5)
            fb = scrape_team_article(t)
            if fb:
                players.extend(fb)
                print(f"  fallback {t}: +{len(fb)}")
            else:
                print(f"  MISSING {t}")
    df = pd.DataFrame([p.__dict__ for p in players])
    df = df.drop_duplicates(subset=["team", "player_name"]).reset_index(drop=True)
    df.to_parquet(OUT, index=False)
    print(f"wrote {OUT} ({len(df)} rows, {df['team'].nunique()} teams)")
    return OUT


if __name__ == "__main__":
    main()
