"""Augment WC2026 venues with Wikipedia infobox fields.

For each of the 16 venues we hit the English Wikipedia page and pull from the
stadium infobox: surface, pitch dimensions (m x m), year opened, owner,
record/average attendance, indoor flag confirmation.

Wikipedia infoboxes vary in label wording; we apply a tolerant matcher with a
hand-curated synonym map. Missing fields are left as NA — never fabricated.

Output: data/processed/venues_enriched.parquet
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

OUT_PATH = Path("data/processed/venues_enriched.parquet")
HEADERS = {"User-Agent": "wc2026-quiniela/0.1 (github.com/DanielRegaladoUMiami/wc2026-quiniela)"}

# Map of venue key -> Wikipedia page title (English).
VENUE_WIKI: dict[str, str] = {
    "mexico_city": "Estadio_Azteca",
    "guadalajara": "Estadio_Akron",
    "monterrey": "Estadio_BBVA",
    "toronto": "BMO_Field",
    "vancouver": "BC_Place",
    "atlanta": "Mercedes-Benz_Stadium",
    "boston": "Gillette_Stadium",
    "dallas": "AT%26T_Stadium",
    "houston": "NRG_Stadium",
    "kansas_city": "Arrowhead_Stadium",
    "los_angeles": "SoFi_Stadium",
    "miami": "Hard_Rock_Stadium",
    "new_york": "MetLife_Stadium",
    "philadelphia": "Lincoln_Financial_Field",
    "san_francisco": "Levi%27s_Stadium",
    "seattle": "Lumen_Field",
}

SYNONYMS: dict[str, list[str]] = {
    "surface": ["surface"],
    "pitch_size_raw": ["field size", "pitch size", "dimensions", "field dimensions"],
    "year_opened": ["opened", "built", "broke ground"],
    "owner": ["owner", "owners"],
    "attendance_avg": ["attendance", "average attendance"],
    "record_attendance": ["record attendance"],
    "capacity": ["capacity"],
}

DIM_RE = re.compile(
    r"(\d{2,3})\s*(?:m|metres|meters)?\s*[x×]\s*(\d{2,3})\s*(?:m|metres|meters)?", re.I
)
YEAR_RE = re.compile(r"(19\d{2}|20\d{2})")


@dataclass
class VenueExtras:
    key: str
    wiki_url: str
    surface: str | None = None
    pitch_length_m: float | None = None
    pitch_width_m: float | None = None
    year_opened: int | None = None
    owner: str | None = None
    attendance_avg: int | None = None
    record_attendance: int | None = None
    wiki_capacity: int | None = None
    indoor_confirmed: bool | None = None


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=2, max=15))
def _fetch(url: str) -> str:
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.text


def _parse_int(s: str) -> int | None:
    """Grab the first integer-like token (handles commas) from the head of a string."""
    s = s.split("(")[0].split("[")[0]
    m = re.search(r"\d{1,3}(?:,\d{3})+|\d{2,7}", s)
    if not m:
        return None
    return int(m.group(0).replace(",", ""))


def parse_infobox(html: str) -> dict[str, str]:
    soup = BeautifulSoup(html, "lxml")
    box = soup.find("table", class_=re.compile(r"infobox"))
    if not box:
        return {}
    out: dict[str, str] = {}
    for tr in box.find_all("tr"):
        th = tr.find("th")
        td = tr.find("td")
        if not th or not td:
            continue
        label = th.get_text(" ", strip=True).lower()
        value = td.get_text(" ", strip=True)
        out[label] = value
    return out


def _match(fields: dict[str, str], keys: list[str]) -> str | None:
    for k in keys:
        for label, val in fields.items():
            if k in label:
                return val
    return None


def extract(key: str, title: str) -> VenueExtras:
    url = f"https://en.wikipedia.org/wiki/{title}"
    try:
        html = _fetch(url)
    except Exception as e:
        print(f"[{key}] fetch failed: {e}")
        return VenueExtras(key=key, wiki_url=url)
    fields = parse_infobox(html)
    extras = VenueExtras(key=key, wiki_url=url)

    if surf := _match(fields, SYNONYMS["surface"]):
        extras.surface = surf.lower().split("(")[0].strip()
    if (dims := _match(fields, SYNONYMS["pitch_size_raw"])) and (m := DIM_RE.search(dims)):
        extras.pitch_length_m = float(m.group(1))
        extras.pitch_width_m = float(m.group(2))
    if (yo := _match(fields, SYNONYMS["year_opened"])) and (m := YEAR_RE.search(yo)):
        extras.year_opened = int(m.group(1))
    if owner := _match(fields, SYNONYMS["owner"]):
        extras.owner = owner.split("[")[0].strip()
    if att := _match(fields, ["average attendance"]):
        extras.attendance_avg = _parse_int(att)
    if rec := _match(fields, SYNONYMS["record_attendance"]):
        extras.record_attendance = _parse_int(rec)
    if cap := _match(fields, SYNONYMS["capacity"]):
        extras.wiki_capacity = _parse_int(cap)
    blob = " ".join(fields.values()).lower()
    if "retractable roof" in blob or "fixed roof" in blob or "indoor" in blob or "dome" in blob:
        extras.indoor_confirmed = ("indoor" in blob) or ("dome" in blob) or ("fixed roof" in blob)
    return extras


def build(venues_path: str = "data/fixtures/venues.parquet") -> pd.DataFrame:
    venues = pd.read_parquet(venues_path)
    rows: list[dict] = []
    for _, v in venues.iterrows():
        key = str(v["key"])
        title = VENUE_WIKI.get(key)
        if not title:
            print(f"[{key}] no wiki mapping")
            rows.append({**v.to_dict(), **VenueExtras(key=key, wiki_url="").__dict__})
            continue
        extras = extract(key, title)
        rows.append({**v.to_dict(), **extras.__dict__})
    # de-dupe 'key' col coming from both venues and extras
    df = pd.DataFrame(rows)
    df = df.loc[:, ~df.columns.duplicated()]
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT_PATH, index=False)
    return df


def main() -> None:
    df = build()
    filled = df["surface"].notna().sum() if "surface" in df else 0
    print(f"wrote {len(df)} venues -> {OUT_PATH}  surface_filled={filled}/{len(df)}")


if __name__ == "__main__":
    main()
