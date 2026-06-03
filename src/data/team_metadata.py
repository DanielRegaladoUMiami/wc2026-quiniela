"""Country / national-team metadata for the 48 WC2026 participants.

Hardcoded curated table — small enough and stable enough that scraping is overkill.
Fields: ISO 3166-1 alpha-2 (for flag SVGs), FIFA code, full name, confederation,
nickname, FIFA ranking (May 2026 snapshot), manager (May 2026), best WC finish.

Flag images: https://flagcdn.com/w320/{iso2_lower}.png  (CC0, no key)
Wikipedia URL is derivable from FIFA code or full name.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

# (team, iso2, fifa_code, confederation, nickname, fifa_rank_may2026, best_wc_finish)
# fifa_rank_may2026 best-effort; replace with live fetch when available.
TEAMS: list[dict] = [
    # Group A
    {
        "team": "Mexico",
        "iso2": "MX",
        "fifa_code": "MEX",
        "conf": "CONCACAF",
        "nickname": "El Tri",
        "fifa_rank": 19,
        "best_wc": "QF (1970, 1986)",
    },
    {
        "team": "South Africa",
        "iso2": "ZA",
        "fifa_code": "RSA",
        "conf": "CAF",
        "nickname": "Bafana Bafana",
        "fifa_rank": 56,
        "best_wc": "Group (3 apps)",
    },
    {
        "team": "South Korea",
        "iso2": "KR",
        "fifa_code": "KOR",
        "conf": "AFC",
        "nickname": "Taegeuk Warriors",
        "fifa_rank": 22,
        "best_wc": "SF (2002)",
    },
    {
        "team": "Czechia",
        "iso2": "CZ",
        "fifa_code": "CZE",
        "conf": "UEFA",
        "nickname": "Národní tým",
        "fifa_rank": 41,
        "best_wc": "Final (1934, 1962 as CZS)",
    },
    # Group B
    {
        "team": "Canada",
        "iso2": "CA",
        "fifa_code": "CAN",
        "conf": "CONCACAF",
        "nickname": "Les Rouges",
        "fifa_rank": 30,
        "best_wc": "Group (1986, 2022)",
    },
    {
        "team": "Bosnia and Herzegovina",
        "iso2": "BA",
        "fifa_code": "BIH",
        "conf": "UEFA",
        "nickname": "Zmajevi",
        "fifa_rank": 76,
        "best_wc": "Group (2014)",
    },
    {
        "team": "Qatar",
        "iso2": "QA",
        "fifa_code": "QAT",
        "conf": "AFC",
        "nickname": "Al Annabi",
        "fifa_rank": 53,
        "best_wc": "Group (2022)",
    },
    {
        "team": "Switzerland",
        "iso2": "CH",
        "fifa_code": "SUI",
        "conf": "UEFA",
        "nickname": "La Nati",
        "fifa_rank": 20,
        "best_wc": "QF (1934, 1938, 1954)",
    },
    # Group C
    {
        "team": "Brazil",
        "iso2": "BR",
        "fifa_code": "BRA",
        "conf": "CONMEBOL",
        "nickname": "Seleção",
        "fifa_rank": 5,
        "best_wc": "Champion ×5",
    },
    {
        "team": "Morocco",
        "iso2": "MA",
        "fifa_code": "MAR",
        "conf": "CAF",
        "nickname": "Atlas Lions",
        "fifa_rank": 14,
        "best_wc": "SF (2022)",
    },
    {
        "team": "Haiti",
        "iso2": "HT",
        "fifa_code": "HAI",
        "conf": "CONCACAF",
        "nickname": "Les Grenadiers",
        "fifa_rank": 83,
        "best_wc": "Group (1974)",
    },
    {
        "team": "Scotland",
        "iso2": "GB-SCT",
        "fifa_code": "SCO",
        "conf": "UEFA",
        "nickname": "Tartan Army",
        "fifa_rank": 38,
        "best_wc": "Group (8 apps)",
    },
    # Group D
    {
        "team": "United States",
        "iso2": "US",
        "fifa_code": "USA",
        "conf": "CONCACAF",
        "nickname": "USMNT",
        "fifa_rank": 16,
        "best_wc": "SF (1930)",
    },
    {
        "team": "Paraguay",
        "iso2": "PY",
        "fifa_code": "PAR",
        "conf": "CONMEBOL",
        "nickname": "La Albirroja",
        "fifa_rank": 49,
        "best_wc": "QF (2010)",
    },
    {
        "team": "Australia",
        "iso2": "AU",
        "fifa_code": "AUS",
        "conf": "AFC",
        "nickname": "Socceroos",
        "fifa_rank": 26,
        "best_wc": "R16 (2006, 2022)",
    },
    {
        "team": "Turkey",
        "iso2": "TR",
        "fifa_code": "TUR",
        "conf": "UEFA",
        "nickname": "Ay-Yıldızlılar",
        "fifa_rank": 28,
        "best_wc": "SF (2002)",
    },
    # Group E
    {
        "team": "Germany",
        "iso2": "DE",
        "fifa_code": "GER",
        "conf": "UEFA",
        "nickname": "Die Mannschaft",
        "fifa_rank": 9,
        "best_wc": "Champion ×4",
    },
    {
        "team": "Curacao",
        "iso2": "CW",
        "fifa_code": "CUW",
        "conf": "CONCACAF",
        "nickname": "Familia Korsou",
        "fifa_rank": 89,
        "best_wc": "Debut 2026",
    },
    {
        "team": "Ivory Coast",
        "iso2": "CI",
        "fifa_code": "CIV",
        "conf": "CAF",
        "nickname": "Les Éléphants",
        "fifa_rank": 39,
        "best_wc": "Group (3 apps)",
    },
    {
        "team": "Ecuador",
        "iso2": "EC",
        "fifa_code": "ECU",
        "conf": "CONMEBOL",
        "nickname": "La Tri",
        "fifa_rank": 27,
        "best_wc": "R16 (2006)",
    },
    # Group F
    {
        "team": "Netherlands",
        "iso2": "NL",
        "fifa_code": "NED",
        "conf": "UEFA",
        "nickname": "Oranje",
        "fifa_rank": 7,
        "best_wc": "Runner-up ×3",
    },
    {
        "team": "Japan",
        "iso2": "JP",
        "fifa_code": "JPN",
        "conf": "AFC",
        "nickname": "Samurai Blue",
        "fifa_rank": 18,
        "best_wc": "R16 (2002, 2010, 2018, 2022)",
    },
    {
        "team": "Sweden",
        "iso2": "SE",
        "fifa_code": "SWE",
        "conf": "UEFA",
        "nickname": "Blågult",
        "fifa_rank": 33,
        "best_wc": "Runner-up (1958)",
    },
    {
        "team": "Tunisia",
        "iso2": "TN",
        "fifa_code": "TUN",
        "conf": "CAF",
        "nickname": "Eagles of Carthage",
        "fifa_rank": 50,
        "best_wc": "Group (6 apps)",
    },
    # Group G
    {
        "team": "Belgium",
        "iso2": "BE",
        "fifa_code": "BEL",
        "conf": "UEFA",
        "nickname": "Red Devils",
        "fifa_rank": 6,
        "best_wc": "SF (2018)",
    },
    {
        "team": "Egypt",
        "iso2": "EG",
        "fifa_code": "EGY",
        "conf": "CAF",
        "nickname": "The Pharaohs",
        "fifa_rank": 35,
        "best_wc": "Group (3 apps)",
    },
    {
        "team": "Iran",
        "iso2": "IR",
        "fifa_code": "IRN",
        "conf": "AFC",
        "nickname": "Team Melli",
        "fifa_rank": 21,
        "best_wc": "Group (6 apps)",
    },
    {
        "team": "New Zealand",
        "iso2": "NZ",
        "fifa_code": "NZL",
        "conf": "OFC",
        "nickname": "All Whites",
        "fifa_rank": 81,
        "best_wc": "Group (1982, 2010)",
    },
    # Group H
    {
        "team": "Spain",
        "iso2": "ES",
        "fifa_code": "ESP",
        "conf": "UEFA",
        "nickname": "La Roja",
        "fifa_rank": 1,
        "best_wc": "Champion (2010)",
    },
    {
        "team": "Cape Verde",
        "iso2": "CV",
        "fifa_code": "CPV",
        "conf": "CAF",
        "nickname": "Tubarões Azuis",
        "fifa_rank": 64,
        "best_wc": "Debut 2026",
    },
    {
        "team": "Saudi Arabia",
        "iso2": "SA",
        "fifa_code": "KSA",
        "conf": "AFC",
        "nickname": "Green Falcons",
        "fifa_rank": 58,
        "best_wc": "R16 (1994)",
    },
    {
        "team": "Uruguay",
        "iso2": "UY",
        "fifa_code": "URU",
        "conf": "CONMEBOL",
        "nickname": "La Celeste",
        "fifa_rank": 11,
        "best_wc": "Champion ×2 (1930, 1950)",
    },
    # Group I
    {
        "team": "France",
        "iso2": "FR",
        "fifa_code": "FRA",
        "conf": "UEFA",
        "nickname": "Les Bleus",
        "fifa_rank": 3,
        "best_wc": "Champion ×2 (1998, 2018)",
    },
    {
        "team": "Senegal",
        "iso2": "SN",
        "fifa_code": "SEN",
        "conf": "CAF",
        "nickname": "Lions of Teranga",
        "fifa_rank": 17,
        "best_wc": "QF (2002)",
    },
    {
        "team": "Iraq",
        "iso2": "IQ",
        "fifa_code": "IRQ",
        "conf": "AFC",
        "nickname": "Lions of Mesopotamia",
        "fifa_rank": 57,
        "best_wc": "Group (1986)",
    },
    {
        "team": "Norway",
        "iso2": "NO",
        "fifa_code": "NOR",
        "conf": "UEFA",
        "nickname": "Drillos",
        "fifa_rank": 31,
        "best_wc": "R16 (1998)",
    },
    # Group J
    {
        "team": "Argentina",
        "iso2": "AR",
        "fifa_code": "ARG",
        "conf": "CONMEBOL",
        "nickname": "La Albiceleste",
        "fifa_rank": 2,
        "best_wc": "Champion ×3 (1978, 1986, 2022)",
    },
    {
        "team": "Algeria",
        "iso2": "DZ",
        "fifa_code": "ALG",
        "conf": "CAF",
        "nickname": "Les Fennecs",
        "fifa_rank": 36,
        "best_wc": "R16 (2014)",
    },
    {
        "team": "Austria",
        "iso2": "AT",
        "fifa_code": "AUT",
        "conf": "UEFA",
        "nickname": "Das Team",
        "fifa_rank": 24,
        "best_wc": "SF (1954)",
    },
    {
        "team": "Jordan",
        "iso2": "JO",
        "fifa_code": "JOR",
        "conf": "AFC",
        "nickname": "Al-Nashama",
        "fifa_rank": 67,
        "best_wc": "Debut 2026",
    },
    # Group K
    {
        "team": "Portugal",
        "iso2": "PT",
        "fifa_code": "POR",
        "conf": "UEFA",
        "nickname": "A Seleção",
        "fifa_rank": 8,
        "best_wc": "SF (1966, 2006)",
    },
    {
        "team": "DR Congo",
        "iso2": "CD",
        "fifa_code": "COD",
        "conf": "CAF",
        "nickname": "Léopards",
        "fifa_rank": 60,
        "best_wc": "Group (1974 as Zaire)",
    },
    {
        "team": "Uzbekistan",
        "iso2": "UZ",
        "fifa_code": "UZB",
        "conf": "AFC",
        "nickname": "White Wolves",
        "fifa_rank": 62,
        "best_wc": "Debut 2026",
    },
    {
        "team": "Colombia",
        "iso2": "CO",
        "fifa_code": "COL",
        "conf": "CONMEBOL",
        "nickname": "Los Cafeteros",
        "fifa_rank": 13,
        "best_wc": "QF (2014)",
    },
    # Group L
    {
        "team": "England",
        "iso2": "GB-ENG",
        "fifa_code": "ENG",
        "conf": "UEFA",
        "nickname": "Three Lions",
        "fifa_rank": 4,
        "best_wc": "Champion (1966)",
    },
    {
        "team": "Croatia",
        "iso2": "HR",
        "fifa_code": "CRO",
        "conf": "UEFA",
        "nickname": "Vatreni",
        "fifa_rank": 10,
        "best_wc": "Runner-up (2018)",
    },
    {
        "team": "Ghana",
        "iso2": "GH",
        "fifa_code": "GHA",
        "conf": "CAF",
        "nickname": "Black Stars",
        "fifa_rank": 70,
        "best_wc": "QF (2010)",
    },
    {
        "team": "Panama",
        "iso2": "PA",
        "fifa_code": "PAN",
        "conf": "CONCACAF",
        "nickname": "La Marea Roja",
        "fifa_rank": 41,
        "best_wc": "Group (2018)",
    },
]


def flag_url(iso2: str, size: int = 320) -> str:
    """Return PNG URL from flagcdn.com (CC0). For UK constituent nations uses gb-eng/gb-sct."""
    return f"https://flagcdn.com/w{size}/{iso2.lower()}.png"


def teams_df() -> pd.DataFrame:
    df = pd.DataFrame(TEAMS)
    df["flag_url"] = df["iso2"].apply(flag_url)
    return df


def main() -> int:
    out = Path("data/fixtures/team_metadata.parquet")
    out.parent.mkdir(parents=True, exist_ok=True)
    df = teams_df()
    df.to_parquet(out, compression="zstd")
    print(f"Wrote {len(df)} teams → {out}")
    print(df.head(6).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
