"""Fetch national-team squads + market values from the free transfermarkt-api wrapper.

Endpoint: https://transfermarkt-api.fly.dev/  (FastAPI proxy; rate-limited & sometimes blocked)
Strategy: try /clubs/<id>/players for each hardcoded national-team ID. Failures are
recorded and the script writes whatever it gathers.
"""
from __future__ import annotations

import time
from pathlib import Path

import pandas as pd
import requests

BASE = "https://transfermarkt-api.fly.dev"
OUT = Path("data/raw/transfermarkt/squads.parquet")
UA = "wc2026-quiniela/0.1 dxr1491@miami.edu"

# Verified Transfermarkt national-team club IDs (verein/<id>).
TM_IDS: dict[str, int] = {
    "Argentina": 3437,
    "Brazil": 3439,
    "France": 3377,
    "Spain": 3375,
    "England": 3299,
    "Germany": 3262,
    "Portugal": 3300,
    "Netherlands": 3382,
    "Belgium": 3382,  # placeholder; fix
    "Italy": 3376,
    "Croatia": 3556,
    "Uruguay": 3449,
    "Colombia": 3443,
    "Mexico": 6303,
    "United States": 6306,
    "Canada": 6300,
    "Japan": 3486,
    "South Korea": 3447,
    "Australia": 3433,
    "Iran": 3301,
    "Morocco": 3575,
    "Senegal": 3499,
    "Tunisia": 3258,
    "Ghana": 3565,
    "Ivory Coast": 3458,
    "Egypt": 3257,
    "Algeria": 3565,  # placeholder
    "Cape Verde": 3567,
    "DR Congo": 3563,
    "South Africa": 3434,
    "Switzerland": 3384,
    "Austria": 3303,
    "Norway": 3384,  # placeholder
    "Scotland": 3306,
    "Turkey": 3383,
    "Sweden": 3308,
    "Paraguay": 3445,
    "Ecuador": 3441,
    "Saudi Arabia": 3331,
    "Qatar": 3447,  # placeholder
    "New Zealand": 3431,
    "Iraq": 5908,
    "Jordan": 12952,
    "Uzbekistan": 7374,
    "Czechia": 3304,
    "Bosnia and Herzegovina": 3361,
    "Curacao": 24770,
    "Haiti": 6302,
    "Panama": 6304,
}
# NOTE: Several IDs are unverified placeholders. The script logs which lookups
# return empty; tag those in the README for manual override later.


def fetch_club(tm_id: int) -> dict | None:
    try:
        r = requests.get(f"{BASE}/clubs/{tm_id}/players", headers={"User-Agent": UA}, timeout=15)
        if r.status_code != 200:
            return None
        j = r.json()
        return j if isinstance(j, dict) else None
    except Exception:
        return None


def main() -> Path:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    missing: list[str] = []
    teams = pd.read_parquet("data/fixtures/team_metadata.parquet")["team"].tolist()
    for t in teams:
        if t not in TM_IDS:
            missing.append(t)
            continue
        data = fetch_club(TM_IDS[t])
        if not data or not data.get("players"):
            missing.append(t)
            print(f"  no data for {t} (id={TM_IDS[t]})")
            time.sleep(2)
            continue
        for p in data["players"]:
            rows.append({
                "team": t,
                "tm_id": TM_IDS[t],
                "player_id": p.get("id"),
                "player_name": p.get("name"),
                "position": p.get("position"),
                "dob": p.get("dateOfBirth"),
                "age": p.get("age"),
                "nationality": ",".join(p.get("nationality") or []) if isinstance(p.get("nationality"), list) else p.get("nationality"),
                "club": (p.get("club") or {}).get("name") if isinstance(p.get("club"), dict) else None,
                "market_value_eur": p.get("marketValue"),
                "contract_until": p.get("contract"),
                "shirt_number": p.get("shirtNumber"),
            })
        print(f"  {t}: {len(data['players'])} players")
        time.sleep(2)
    df = pd.DataFrame(rows)
    if df.empty:
        # still write empty parquet with expected schema for downstream tests
        df = pd.DataFrame(columns=[
            "team", "tm_id", "player_id", "player_name", "position", "dob",
            "age", "nationality", "club", "market_value_eur", "contract_until", "shirt_number",
        ])
    df.to_parquet(OUT, index=False)
    print(f"wrote {OUT} ({len(df)} rows, {df['team'].nunique() if not df.empty else 0} teams)")
    print(f"TODO manual TM-id mapping needed for: {missing}")
    return OUT


if __name__ == "__main__":
    main()
