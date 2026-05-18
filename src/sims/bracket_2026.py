"""FIFA World Cup 2026 official fixture topology and venue catalog.

Source: FIFA final draw 5 Dec 2025 (Kennedy Center, Washington DC). Schedule + venues
cross-referenced with Wikipedia, fifa.com, Sky Sports, MLSSoccer, NBC Sports.

Format: 48 teams in 12 groups (A-L) of 4. 104 matches. Top 2 of each group + 8 best
third-placed teams advance to Round of 32, then standard knockout to the Final on
July 19, 2026 at MetLife Stadium (East Rutherford, NY/NJ).

Stage codes: "group", "R32", "R16", "QF", "SF", "3rd", "final"
Position codes: "1A"/"2A"/"3X/Y/Z/..."=group standings;  "W##"/"L##"=match outcomes.

Caveat: FIFA's exact mapping of third-placed groups to R32 slots is governed by a
published 12-choose-8 lookup table (regulations PDF). Until that table is loaded into
data/fixtures/third_placed_lookup.yaml the third-placed pairings are stochastic —
simulation code should sample one of the listed groups uniformly as a placeholder.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import polars as pl


GROUPS: dict[str, list[str]] = {
    "A": ["Mexico", "South Africa", "South Korea", "Czechia"],
    "B": ["Canada", "Bosnia and Herzegovina", "Qatar", "Switzerland"],
    "C": ["Brazil", "Morocco", "Haiti", "Scotland"],
    "D": ["United States", "Paraguay", "Australia", "Turkey"],
    "E": ["Germany", "Curacao", "Ivory Coast", "Ecuador"],
    "F": ["Netherlands", "Japan", "Sweden", "Tunisia"],
    "G": ["Belgium", "Egypt", "Iran", "New Zealand"],
    "H": ["Spain", "Cape Verde", "Saudi Arabia", "Uruguay"],
    "I": ["France", "Senegal", "Iraq", "Norway"],
    "J": ["Argentina", "Algeria", "Austria", "Jordan"],
    "K": ["Portugal", "DR Congo", "Uzbekistan", "Colombia"],
    "L": ["England", "Croatia", "Ghana", "Panama"],
}


VENUES: list[dict] = [
    {"key": "mexico_city",   "stadium": "Estadio Azteca",           "city": "Mexico City",                    "country": "Mexico", "lat": 19.3029, "lon":  -99.1505, "altitude_m": 2240, "capacity": 83264, "indoor": False, "roof": "open"},
    {"key": "guadalajara",   "stadium": "Estadio Akron",            "city": "Zapopan (Guadalajara)",          "country": "Mexico", "lat": 20.6818, "lon": -103.4624, "altitude_m": 1560, "capacity": 48071, "indoor": False, "roof": "open"},
    {"key": "monterrey",     "stadium": "Estadio BBVA",             "city": "Guadalupe (Monterrey)",          "country": "Mexico", "lat": 25.6692, "lon": -100.2444, "altitude_m":  500, "capacity": 53500, "indoor": False, "roof": "open"},
    {"key": "toronto",       "stadium": "BMO Field",                "city": "Toronto",                        "country": "Canada", "lat": 43.6332, "lon":  -79.4185, "altitude_m":   76, "capacity": 45736, "indoor": False, "roof": "open"},
    {"key": "vancouver",     "stadium": "BC Place",                 "city": "Vancouver",                      "country": "Canada", "lat": 49.2767, "lon": -123.1118, "altitude_m":    0, "capacity": 54500, "indoor": False, "roof": "retractable"},
    {"key": "atlanta",       "stadium": "Mercedes-Benz Stadium",    "city": "Atlanta",                        "country": "USA",    "lat": 33.7553, "lon":  -84.4006, "altitude_m":  320, "capacity": 71000, "indoor": True,  "roof": "retractable"},
    {"key": "boston",        "stadium": "Gillette Stadium",         "city": "Foxborough (Boston)",            "country": "USA",    "lat": 42.0909, "lon":  -71.2643, "altitude_m":   78, "capacity": 65878, "indoor": False, "roof": "open"},
    {"key": "dallas",        "stadium": "AT&T Stadium",             "city": "Arlington (Dallas)",             "country": "USA",    "lat": 32.7473, "lon":  -97.0945, "altitude_m":  170, "capacity": 80000, "indoor": True,  "roof": "retractable"},
    {"key": "houston",       "stadium": "NRG Stadium",              "city": "Houston",                        "country": "USA",    "lat": 29.6847, "lon":  -95.4107, "altitude_m":   15, "capacity": 72220, "indoor": True,  "roof": "retractable"},
    {"key": "kansas_city",   "stadium": "Arrowhead Stadium",        "city": "Kansas City",                    "country": "USA",    "lat": 39.0489, "lon":  -94.4839, "altitude_m":  240, "capacity": 76416, "indoor": False, "roof": "open"},
    {"key": "los_angeles",   "stadium": "SoFi Stadium",             "city": "Inglewood (Los Angeles)",        "country": "USA",    "lat": 33.9535, "lon": -118.3392, "altitude_m":   30, "capacity": 70240, "indoor": False, "roof": "fixed canopy"},
    {"key": "miami",         "stadium": "Hard Rock Stadium",        "city": "Miami Gardens",                  "country": "USA",    "lat": 25.9580, "lon":  -80.2389, "altitude_m":    2, "capacity": 65326, "indoor": False, "roof": "open"},
    {"key": "new_york",      "stadium": "MetLife Stadium",          "city": "East Rutherford (NY/NJ)",        "country": "USA",    "lat": 40.8135, "lon":  -74.0745, "altitude_m":    2, "capacity": 82500, "indoor": False, "roof": "open"},
    {"key": "philadelphia",  "stadium": "Lincoln Financial Field",  "city": "Philadelphia",                   "country": "USA",    "lat": 39.9008, "lon":  -75.1675, "altitude_m":   10, "capacity": 69796, "indoor": False, "roof": "open"},
    {"key": "san_francisco", "stadium": "Levi's Stadium",           "city": "Santa Clara (SF Bay)",           "country": "USA",    "lat": 37.4030, "lon": -121.9698, "altitude_m":    5, "capacity": 68500, "indoor": False, "roof": "open"},
    {"key": "seattle",       "stadium": "Lumen Field",              "city": "Seattle",                        "country": "USA",    "lat": 47.5952, "lon": -122.3316, "altitude_m":    5, "capacity": 68740, "indoor": False, "roof": "partial canopy"},
]


GROUP_MATCHES: list[dict] = [
    # Group A
    {"num":  1, "date": "2026-06-11", "venue": "mexico_city",  "stage": "group", "group": "A", "home": "Mexico",         "away": "South Africa"},
    {"num":  2, "date": "2026-06-12", "venue": "guadalajara",  "stage": "group", "group": "A", "home": "South Korea",    "away": "Czechia"},
    {"num": 19, "date": "2026-06-18", "venue": "atlanta",      "stage": "group", "group": "A", "home": "Czechia",        "away": "South Africa"},
    {"num": 22, "date": "2026-06-18", "venue": "guadalajara",  "stage": "group", "group": "A", "home": "Mexico",         "away": "South Korea"},
    {"num": 49, "date": "2026-06-24", "venue": "monterrey",    "stage": "group", "group": "A", "home": "South Africa",   "away": "South Korea"},
    {"num": 50, "date": "2026-06-24", "venue": "mexico_city",  "stage": "group", "group": "A", "home": "Czechia",        "away": "Mexico"},
    # Group B
    {"num":  4, "date": "2026-06-12", "venue": "toronto",      "stage": "group", "group": "B", "home": "Canada",         "away": "Bosnia and Herzegovina"},
    {"num":  8, "date": "2026-06-13", "venue": "san_francisco","stage": "group", "group": "B", "home": "Qatar",          "away": "Switzerland"},
    {"num": 20, "date": "2026-06-18", "venue": "los_angeles",  "stage": "group", "group": "B", "home": "Switzerland",    "away": "Bosnia and Herzegovina"},
    {"num": 24, "date": "2026-06-18", "venue": "vancouver",    "stage": "group", "group": "B", "home": "Canada",         "away": "Qatar"},
    {"num": 51, "date": "2026-06-24", "venue": "vancouver",    "stage": "group", "group": "B", "home": "Switzerland",    "away": "Canada"},
    {"num": 52, "date": "2026-06-24", "venue": "seattle",      "stage": "group", "group": "B", "home": "Bosnia and Herzegovina", "away": "Qatar"},
    # Group C
    {"num":  7, "date": "2026-06-13", "venue": "new_york",     "stage": "group", "group": "C", "home": "Brazil",         "away": "Morocco"},
    {"num": 11, "date": "2026-06-13", "venue": "boston",       "stage": "group", "group": "C", "home": "Haiti",          "away": "Scotland"},
    {"num": 26, "date": "2026-06-19", "venue": "boston",       "stage": "group", "group": "C", "home": "Scotland",       "away": "Morocco"},
    {"num": 30, "date": "2026-06-19", "venue": "philadelphia", "stage": "group", "group": "C", "home": "Brazil",         "away": "Haiti"},
    {"num": 55, "date": "2026-06-24", "venue": "miami",        "stage": "group", "group": "C", "home": "Scotland",       "away": "Brazil"},
    {"num": 56, "date": "2026-06-24", "venue": "atlanta",      "stage": "group", "group": "C", "home": "Morocco",        "away": "Haiti"},
    # Group D
    {"num":  5, "date": "2026-06-12", "venue": "los_angeles",  "stage": "group", "group": "D", "home": "United States",  "away": "Paraguay"},
    {"num": 12, "date": "2026-06-13", "venue": "vancouver",    "stage": "group", "group": "D", "home": "Australia",      "away": "Turkey"},
    {"num": 25, "date": "2026-06-19", "venue": "seattle",      "stage": "group", "group": "D", "home": "United States",  "away": "Australia"},
    {"num": 29, "date": "2026-06-19", "venue": "san_francisco","stage": "group", "group": "D", "home": "Turkey",         "away": "Paraguay"},
    {"num": 59, "date": "2026-06-25", "venue": "los_angeles",  "stage": "group", "group": "D", "home": "Turkey",         "away": "United States"},
    {"num": 60, "date": "2026-06-25", "venue": "san_francisco","stage": "group", "group": "D", "home": "Paraguay",       "away": "Australia"},
    # Group E
    {"num": 13, "date": "2026-06-14", "venue": "houston",      "stage": "group", "group": "E", "home": "Germany",        "away": "Curacao"},
    {"num": 16, "date": "2026-06-14", "venue": "philadelphia", "stage": "group", "group": "E", "home": "Ivory Coast",    "away": "Ecuador"},
    {"num": 31, "date": "2026-06-20", "venue": "toronto",      "stage": "group", "group": "E", "home": "Germany",        "away": "Ivory Coast"},
    {"num": 35, "date": "2026-06-20", "venue": "kansas_city",  "stage": "group", "group": "E", "home": "Ecuador",        "away": "Curacao"},
    {"num": 61, "date": "2026-06-25", "venue": "philadelphia", "stage": "group", "group": "E", "home": "Curacao",        "away": "Ivory Coast"},
    {"num": 62, "date": "2026-06-25", "venue": "new_york",     "stage": "group", "group": "E", "home": "Ecuador",        "away": "Germany"},
    # Group F
    {"num":  9, "date": "2026-06-13", "venue": "dallas",       "stage": "group", "group": "F", "home": "Netherlands",    "away": "Japan"},
    {"num": 14, "date": "2026-06-14", "venue": "monterrey",    "stage": "group", "group": "F", "home": "Sweden",         "away": "Tunisia"},
    {"num": 32, "date": "2026-06-20", "venue": "houston",      "stage": "group", "group": "F", "home": "Netherlands",    "away": "Sweden"},
    {"num": 36, "date": "2026-06-20", "venue": "monterrey",    "stage": "group", "group": "F", "home": "Tunisia",        "away": "Japan"},
    {"num": 63, "date": "2026-06-25", "venue": "kansas_city",  "stage": "group", "group": "F", "home": "Tunisia",        "away": "Netherlands"},
    {"num": 64, "date": "2026-06-25", "venue": "dallas",       "stage": "group", "group": "F", "home": "Japan",          "away": "Sweden"},
    # Group G
    {"num": 17, "date": "2026-06-15", "venue": "seattle",      "stage": "group", "group": "G", "home": "Belgium",        "away": "Egypt"},
    {"num": 21, "date": "2026-06-15", "venue": "los_angeles",  "stage": "group", "group": "G", "home": "Iran",           "away": "New Zealand"},
    {"num": 37, "date": "2026-06-21", "venue": "los_angeles",  "stage": "group", "group": "G", "home": "Belgium",        "away": "Iran"},
    {"num": 41, "date": "2026-06-21", "venue": "vancouver",    "stage": "group", "group": "G", "home": "New Zealand",    "away": "Egypt"},
    {"num": 67, "date": "2026-06-26", "venue": "vancouver",    "stage": "group", "group": "G", "home": "New Zealand",    "away": "Belgium"},
    {"num": 68, "date": "2026-06-26", "venue": "seattle",      "stage": "group", "group": "G", "home": "Egypt",          "away": "Iran"},
    # Group H
    {"num": 15, "date": "2026-06-15", "venue": "atlanta",      "stage": "group", "group": "H", "home": "Spain",          "away": "Cape Verde"},
    {"num": 18, "date": "2026-06-15", "venue": "miami",        "stage": "group", "group": "H", "home": "Saudi Arabia",   "away": "Uruguay"},
    {"num": 38, "date": "2026-06-21", "venue": "atlanta",      "stage": "group", "group": "H", "home": "Spain",          "away": "Saudi Arabia"},
    {"num": 42, "date": "2026-06-21", "venue": "miami",        "stage": "group", "group": "H", "home": "Uruguay",        "away": "Cape Verde"},
    {"num": 65, "date": "2026-06-26", "venue": "houston",      "stage": "group", "group": "H", "home": "Cape Verde",     "away": "Saudi Arabia"},
    {"num": 66, "date": "2026-06-26", "venue": "guadalajara",  "stage": "group", "group": "H", "home": "Uruguay",        "away": "Spain"},
    # Group I
    {"num": 23, "date": "2026-06-16", "venue": "new_york",     "stage": "group", "group": "I", "home": "France",         "away": "Senegal"},
    {"num": 27, "date": "2026-06-16", "venue": "boston",       "stage": "group", "group": "I", "home": "Iraq",           "away": "Norway"},
    {"num": 39, "date": "2026-06-22", "venue": "philadelphia", "stage": "group", "group": "I", "home": "France",         "away": "Iraq"},
    {"num": 43, "date": "2026-06-22", "venue": "toronto",      "stage": "group", "group": "I", "home": "Norway",         "away": "Senegal"},
    {"num": 69, "date": "2026-06-26", "venue": "boston",       "stage": "group", "group": "I", "home": "Norway",         "away": "France"},
    {"num": 70, "date": "2026-06-26", "venue": "toronto",      "stage": "group", "group": "I", "home": "Senegal",        "away": "Iraq"},
    # Group J
    {"num": 28, "date": "2026-06-16", "venue": "kansas_city",  "stage": "group", "group": "J", "home": "Argentina",      "away": "Algeria"},
    {"num": 33, "date": "2026-06-16", "venue": "san_francisco","stage": "group", "group": "J", "home": "Austria",        "away": "Jordan"},
    {"num": 44, "date": "2026-06-22", "venue": "dallas",       "stage": "group", "group": "J", "home": "Argentina",      "away": "Austria"},
    {"num": 47, "date": "2026-06-22", "venue": "san_francisco","stage": "group", "group": "J", "home": "Jordan",         "away": "Algeria"},
    {"num": 71, "date": "2026-06-27", "venue": "kansas_city",  "stage": "group", "group": "J", "home": "Algeria",        "away": "Austria"},
    {"num": 72, "date": "2026-06-27", "venue": "dallas",       "stage": "group", "group": "J", "home": "Jordan",         "away": "Argentina"},
    # Group K
    {"num": 34, "date": "2026-06-17", "venue": "houston",      "stage": "group", "group": "K", "home": "Portugal",       "away": "DR Congo"},
    {"num": 40, "date": "2026-06-17", "venue": "mexico_city",  "stage": "group", "group": "K", "home": "Uzbekistan",     "away": "Colombia"},
    {"num": 45, "date": "2026-06-23", "venue": "houston",      "stage": "group", "group": "K", "home": "Portugal",       "away": "Uzbekistan"},
    {"num": 48, "date": "2026-06-23", "venue": "guadalajara",  "stage": "group", "group": "K", "home": "Colombia",       "away": "DR Congo"},
    {"num": 53, "date": "2026-06-27", "venue": "miami",        "stage": "group", "group": "K", "home": "Colombia",       "away": "Portugal"},
    {"num": 54, "date": "2026-06-27", "venue": "atlanta",      "stage": "group", "group": "K", "home": "DR Congo",       "away": "Uzbekistan"},
    # Group L
    {"num": 46, "date": "2026-06-17", "venue": "dallas",       "stage": "group", "group": "L", "home": "England",        "away": "Croatia"},
    {"num":  3, "date": "2026-06-17", "venue": "toronto",      "stage": "group", "group": "L", "home": "Ghana",          "away": "Panama"},
    {"num":  6, "date": "2026-06-23", "venue": "boston",       "stage": "group", "group": "L", "home": "England",        "away": "Ghana"},
    {"num": 10, "date": "2026-06-23", "venue": "boston",       "stage": "group", "group": "L", "home": "Panama",         "away": "Croatia"},
    {"num": 57, "date": "2026-06-27", "venue": "new_york",     "stage": "group", "group": "L", "home": "Panama",         "away": "England"},
    {"num": 58, "date": "2026-06-27", "venue": "philadelphia", "stage": "group", "group": "L", "home": "Croatia",        "away": "Ghana"},
]


KNOCKOUT_FIXTURES: list[dict] = [
    # Round of 32
    {"num":  77, "date": "2026-06-28", "venue": "los_angeles",  "stage": "R32", "home_pos": "2A",                "away_pos": "2B"},
    {"num":  78, "date": "2026-06-29", "venue": "boston",       "stage": "R32", "home_pos": "1E",                "away_pos": "3A/B/C/D/F"},
    {"num":  79, "date": "2026-06-29", "venue": "monterrey",    "stage": "R32", "home_pos": "1F",                "away_pos": "2C"},
    {"num":  80, "date": "2026-06-29", "venue": "houston",      "stage": "R32", "home_pos": "1C",                "away_pos": "2F"},
    {"num":  81, "date": "2026-06-30", "venue": "new_york",     "stage": "R32", "home_pos": "1I",                "away_pos": "3C/D/F/G/H"},
    {"num":  82, "date": "2026-06-30", "venue": "dallas",       "stage": "R32", "home_pos": "2E",                "away_pos": "2I"},
    {"num":  83, "date": "2026-06-30", "venue": "mexico_city",  "stage": "R32", "home_pos": "1A",                "away_pos": "3C/E/F/H/I"},
    {"num":  84, "date": "2026-07-01", "venue": "atlanta",      "stage": "R32", "home_pos": "1L",                "away_pos": "3E/H/I/J/K"},
    {"num":  85, "date": "2026-07-01", "venue": "san_francisco","stage": "R32", "home_pos": "1D",                "away_pos": "3B/E/F/I/J"},
    {"num":  86, "date": "2026-07-01", "venue": "seattle",      "stage": "R32", "home_pos": "1G",                "away_pos": "3A/E/H/I/J"},
    {"num":  87, "date": "2026-07-02", "venue": "toronto",      "stage": "R32", "home_pos": "2K",                "away_pos": "2L"},
    {"num":  88, "date": "2026-07-02", "venue": "los_angeles",  "stage": "R32", "home_pos": "1H",                "away_pos": "2J"},
    {"num":  89, "date": "2026-07-02", "venue": "vancouver",    "stage": "R32", "home_pos": "1B",                "away_pos": "3E/F/G/I/J"},
    {"num":  90, "date": "2026-07-03", "venue": "miami",        "stage": "R32", "home_pos": "1J",                "away_pos": "2H"},
    {"num":  91, "date": "2026-07-03", "venue": "kansas_city",  "stage": "R32", "home_pos": "1K",                "away_pos": "3D/E/I/J/L"},
    {"num":  92, "date": "2026-07-03", "venue": "dallas",       "stage": "R32", "home_pos": "2D",                "away_pos": "2G"},
    # R16
    {"num":  93, "date": "2026-07-04", "venue": "philadelphia", "stage": "R16",  "home_pos": "W78",  "away_pos": "W81"},
    {"num":  94, "date": "2026-07-04", "venue": "houston",      "stage": "R16",  "home_pos": "W77",  "away_pos": "W79"},
    {"num":  95, "date": "2026-07-05", "venue": "new_york",     "stage": "R16",  "home_pos": "W80",  "away_pos": "W82"},
    {"num":  96, "date": "2026-07-05", "venue": "mexico_city",  "stage": "R16",  "home_pos": "W83",  "away_pos": "W84"},
    {"num":  97, "date": "2026-07-06", "venue": "dallas",       "stage": "R16",  "home_pos": "W87",  "away_pos": "W88"},
    {"num":  98, "date": "2026-07-06", "venue": "seattle",      "stage": "R16",  "home_pos": "W85",  "away_pos": "W86"},
    {"num":  99, "date": "2026-07-07", "venue": "atlanta",      "stage": "R16",  "home_pos": "W90",  "away_pos": "W92"},
    {"num": 100, "date": "2026-07-07", "venue": "vancouver",    "stage": "R16",  "home_pos": "W89",  "away_pos": "W91"},
    # QF
    {"num": 101, "date": "2026-07-09", "venue": "boston",       "stage": "QF",   "home_pos": "W93",  "away_pos": "W94"},
    {"num": 102, "date": "2026-07-10", "venue": "los_angeles",  "stage": "QF",   "home_pos": "W97",  "away_pos": "W98"},
    {"num": 103, "date": "2026-07-11", "venue": "miami",        "stage": "QF",   "home_pos": "W95",  "away_pos": "W96"},
    {"num": 104, "date": "2026-07-11", "venue": "kansas_city",  "stage": "QF",   "home_pos": "W99",  "away_pos": "W100"},
    # SF
    {"num": 105, "date": "2026-07-14", "venue": "dallas",       "stage": "SF",   "home_pos": "W101", "away_pos": "W102"},
    {"num": 106, "date": "2026-07-15", "venue": "atlanta",      "stage": "SF",   "home_pos": "W103", "away_pos": "W104"},
    # 3rd place
    {"num": 107, "date": "2026-07-18", "venue": "miami",        "stage": "3rd",  "home_pos": "L105", "away_pos": "L106"},
    # Final
    {"num": 108, "date": "2026-07-19", "venue": "new_york",     "stage": "final","home_pos": "W105", "away_pos": "W106"},
]


def venues_df() -> pd.DataFrame:
    return pd.DataFrame(VENUES)


def groups_df() -> pd.DataFrame:
    rows = [{"group": g, "team": t} for g, ts in GROUPS.items() for t in ts]
    return pd.DataFrame(rows)


def all_fixtures_df() -> pd.DataFrame:
    """Combined group + knockout fixtures with venue metadata joined."""
    g = pd.DataFrame(GROUP_MATCHES)
    g["home_pos"] = None
    g["away_pos"] = None
    k = pd.DataFrame(KNOCKOUT_FIXTURES)
    k["group"] = None
    k["home"] = None
    k["away"] = None
    cols = ["num", "date", "venue", "stage", "group", "home", "away", "home_pos", "away_pos"]
    fixtures = pd.concat([g[cols], k[cols]], ignore_index=True).sort_values("num").reset_index(drop=True)
    venues = venues_df().rename(columns={"key": "venue"})
    fixtures = fixtures.merge(
        venues[["venue", "stadium", "city", "country", "lat", "lon", "altitude_m", "indoor", "roof"]],
        on="venue",
        how="left",
    )
    fixtures["date"] = pd.to_datetime(fixtures["date"])
    return fixtures


def save_parquets(out_dir: str | Path = "data/fixtures") -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    venues_df().to_parquet(out / "venues.parquet", compression="zstd")
    groups_df().to_parquet(out / "groups.parquet", compression="zstd")
    all_fixtures_df().to_parquet(out / "wc2026_fixtures.parquet", compression="zstd")


if __name__ == "__main__":
    save_parquets()
    print(f"Groups: {len(GROUPS)} ({sum(len(v) for v in GROUPS.values())} teams)")
    print(f"Venues: {len(VENUES)}")
    print(f"Group matches: {len(GROUP_MATCHES)} (expected 72)")
    print(f"Knockout matches: {len(KNOCKOUT_FIXTURES)} (expected 32)")
    print(f"Total: {len(GROUP_MATCHES) + len(KNOCKOUT_FIXTURES)} (expected 104)")
