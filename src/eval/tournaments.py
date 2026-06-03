"""Tournament registry + filter logic for backtest harness.

Each entry defines:
  - competition_match: substring matched against `competition` (case-insensitive,
    exact equality after lowercasing to avoid catching "qualification" rows).
  - year: nominal tournament year (used for naming).
  - start, end: inclusive date bounds the matches must fall within.

Note on edition vs. played year:
  - Euro 2020 was played in summer 2021 (COVID delay).
  - AFCON 2021 was played Jan-Feb 2022; AFCON 2023 was played Jan-Feb 2024.
  - The `year` field reflects the tournament edition; date bounds reflect when it was played.

Filter logic (`select_tournament`) requires:
  - lowercased `competition` field equals lowercased `competition_match`
    (this excludes "FIFA World Cup qualification" rows naturally).
  - `start <= date <= end`.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date

import pandas as pd

TOURNAMENTS: dict[str, dict] = {
    # World Cups
    "wc14": {
        "competition_match": "FIFA World Cup",
        "year": 2014,
        "start": date(2014, 6, 12),
        "end": date(2014, 7, 13),
    },
    "wc18": {
        "competition_match": "FIFA World Cup",
        "year": 2018,
        "start": date(2018, 6, 14),
        "end": date(2018, 7, 15),
    },
    "wc22": {
        "competition_match": "FIFA World Cup",
        "year": 2022,
        "start": date(2022, 11, 20),
        "end": date(2022, 12, 18),
    },
    # UEFA Euros
    "euro16": {
        "competition_match": "UEFA Euro",
        "year": 2016,
        "start": date(2016, 6, 10),
        "end": date(2016, 7, 10),
    },
    "euro20": {
        "competition_match": "UEFA Euro",
        "year": 2020,
        "start": date(2021, 6, 11),
        "end": date(2021, 7, 11),
    },
    "euro24": {
        "competition_match": "UEFA Euro",
        "year": 2024,
        "start": date(2024, 6, 14),
        "end": date(2024, 7, 14),
    },
    # Copa América
    "copa19": {
        "competition_match": "Copa América",
        "year": 2019,
        "start": date(2019, 6, 14),
        "end": date(2019, 7, 7),
    },
    "copa21": {
        "competition_match": "Copa América",
        "year": 2021,
        "start": date(2021, 6, 13),
        "end": date(2021, 7, 10),
    },
    "copa24": {
        "competition_match": "Copa América",
        "year": 2024,
        "start": date(2024, 6, 20),
        "end": date(2024, 7, 14),
    },
    # Africa Cup of Nations
    "afcon19": {
        "competition_match": "African Cup of Nations",
        "year": 2019,
        "start": date(2019, 6, 21),
        "end": date(2019, 7, 19),
    },
    "afcon21": {
        # 2021 edition, played Jan-Feb 2022
        "competition_match": "African Cup of Nations",
        "year": 2021,
        "start": date(2022, 1, 9),
        "end": date(2022, 2, 6),
    },
    "afcon23": {
        # 2023 edition, played Jan-Feb 2024
        "competition_match": "African Cup of Nations",
        "year": 2023,
        "start": date(2024, 1, 13),
        "end": date(2024, 2, 11),
    },
    # AFC Asian Cup
    "asian19": {
        "competition_match": "AFC Asian Cup",
        "year": 2019,
        "start": date(2019, 1, 5),
        "end": date(2019, 2, 1),
    },
    "asian23": {
        # 2023 edition, played Jan-Feb 2024
        "competition_match": "AFC Asian Cup",
        "year": 2023,
        "start": date(2024, 1, 12),
        "end": date(2024, 2, 10),
    },
    # UEFA Nations League (full season window)
    "unl20": {
        "competition_match": "UEFA Nations League",
        "year": 2020,
        "start": date(2020, 9, 3),
        "end": date(2021, 6, 6),
    },
    "unl22": {
        "competition_match": "UEFA Nations League",
        "year": 2022,
        "start": date(2022, 6, 1),
        "end": date(2023, 6, 18),
    },
}


def select_tournament(matches: pd.DataFrame, t: dict) -> pd.DataFrame:
    """Filter `matches` to a single tournament edition.

    Uses exact (case-insensitive) competition equality plus inclusive date bounds.
    Returns a copy sorted by date.
    """
    m = matches.copy()
    m["date"] = pd.to_datetime(m["date"]).dt.date
    comp_match = str(t["competition_match"]).lower()
    mask = (
        (m["date"] >= t["start"])
        & (m["date"] <= t["end"])
        & (m["competition"].astype(str).str.lower() == comp_match)
    )
    return m.loc[mask].sort_values("date").reset_index(drop=True)


def available_keys() -> list[str]:
    return list(TOURNAMENTS.keys())


def resolve_keys(keys: Iterable[str]) -> list[str]:
    out = []
    for k in keys:
        if k not in TOURNAMENTS:
            raise KeyError(f"Unknown tournament key: {k!r}. Available: {available_keys()}")
        out.append(k)
    return out
