"""Weather fetcher for WC2026 fixtures via Open-Meteo (free, no key).

Strategy per fixture, given today's date:
  - If kickoff within forecast horizon (<=16 days ahead): use forecast API.
  - Else: build a climatology baseline from historical June/July of last 5 years
    at the venue lat/lon, averaging hourly values across years for the matching
    day-of-year +/- 3 day window.

APIs:
  - Forecast:  https://api.open-meteo.com/v1/forecast
  - Archive:   https://archive-api.open-meteo.com/v1/archive

Kickoff time heuristic: WC2026 not fully scheduled by hour at parquet ingest time.
Default kickoff_utc = date + 19:00 UTC. Override via --kickoff-hour.

Output: data/processed/venue_weather.parquet
Columns: match_num, venue, kickoff_utc, source, temp_c, humidity_pct,
         wind_kph, precip_mm, cloud_pct, heat_index_c
"""

from __future__ import annotations

import argparse
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
OUT_PATH = Path("data/processed/venue_weather.parquet")
HEADERS = {"User-Agent": "wc2026-quiniela/0.1 (github.com/DanielRegaladoUMiami/wc2026-quiniela)"}

HOURLY_VARS = "temperature_2m,relativehumidity_2m,precipitation,windspeed_10m,cloudcover"


@dataclass
class WeatherRow:
    match_num: int
    venue: str
    kickoff_utc: pd.Timestamp
    source: str
    temp_c: float
    humidity_pct: float
    wind_kph: float
    precip_mm: float
    cloud_pct: float
    heat_index_c: float


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=2, max=20))
def _get(url: str, params: dict) -> dict:
    r = requests.get(url, params=params, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()


def heat_index_c(temp_c: float, humidity_pct: float) -> float:
    """Rothfusz heat-index in Celsius. Returns temp_c if conditions don't warrant HI."""
    if temp_c < 26.7 or humidity_pct < 40:
        return float(temp_c)
    t = temp_c * 9 / 5 + 32  # to F
    rh = humidity_pct
    hi = (
        -42.379 + 2.04901523 * t + 10.14333127 * rh
        - 0.22475541 * t * rh - 6.83783e-3 * t * t
        - 5.481717e-2 * rh * rh + 1.22874e-3 * t * t * rh
        + 8.5282e-4 * t * rh * rh - 1.99e-6 * t * t * rh * rh
    )
    return float((hi - 32) * 5 / 9)


def _pick_hour(payload: dict, target_iso_hour: str) -> dict[str, float] | None:
    hourly = payload.get("hourly")
    if not hourly:
        return None
    times = hourly.get("time", [])
    if target_iso_hour not in times:
        return None
    i = times.index(target_iso_hour)
    return {
        "temp_c": hourly["temperature_2m"][i],
        "humidity_pct": hourly["relativehumidity_2m"][i],
        "precip_mm": hourly["precipitation"][i],
        "wind_kph": hourly["windspeed_10m"][i],
        "cloud_pct": hourly["cloudcover"][i],
    }


def fetch_forecast(lat: float, lon: float, kickoff: pd.Timestamp) -> dict[str, float] | None:
    params = {
        "latitude": lat, "longitude": lon, "hourly": HOURLY_VARS,
        "timezone": "UTC", "windspeed_unit": "kmh", "forecast_days": 16,
    }
    payload = _get(FORECAST_URL, params)
    target = kickoff.strftime("%Y-%m-%dT%H:00")
    return _pick_hour(payload, target)


def fetch_climatology(lat: float, lon: float, kickoff: pd.Timestamp,
                      years_back: int = 5, window_days: int = 3) -> dict[str, float] | None:
    """Average each hourly variable across the last `years_back` years over a
    +/- window_days range around the same calendar day at the kickoff hour."""
    samples: list[dict[str, float]] = []
    now_year = pd.Timestamp.utcnow().year
    for y in range(now_year - years_back, now_year):
        try:
            date = kickoff.replace(year=y)
        except ValueError:
            continue
        start = (date - pd.Timedelta(days=window_days)).strftime("%Y-%m-%d")
        end = (date + pd.Timedelta(days=window_days)).strftime("%Y-%m-%d")
        params = {
            "latitude": lat, "longitude": lon, "start_date": start, "end_date": end,
            "hourly": HOURLY_VARS, "timezone": "UTC", "windspeed_unit": "kmh",
        }
        try:
            payload = _get(ARCHIVE_URL, params)
        except Exception:
            continue
        hourly = payload.get("hourly", {})
        times = hourly.get("time", [])
        for i, t in enumerate(times):
            if t.endswith(f"T{kickoff.hour:02d}:00"):
                samples.append({
                    "temp_c": hourly["temperature_2m"][i],
                    "humidity_pct": hourly["relativehumidity_2m"][i],
                    "precip_mm": hourly["precipitation"][i],
                    "wind_kph": hourly["windspeed_10m"][i],
                    "cloud_pct": hourly["cloudcover"][i],
                })
        time.sleep(0.3)
    if not samples:
        return None
    df = pd.DataFrame(samples)
    return {c: float(np.nanmean(df[c])) for c in df.columns}


def fetch_for_fixture(num: int, venue: str, lat: float, lon: float,
                      kickoff: pd.Timestamp, today: pd.Timestamp | None = None) -> WeatherRow | None:
    today = today or pd.Timestamp.utcnow().tz_localize(None).normalize()
    horizon_end = today + pd.Timedelta(days=16)
    src = "forecast" if (today <= kickoff <= horizon_end) else "climatology"
    try:
        vals = fetch_forecast(lat, lon, kickoff) if src == "forecast" else fetch_climatology(lat, lon, kickoff)
    except Exception:
        vals = None
    if vals is None and src == "forecast":
        vals = fetch_climatology(lat, lon, kickoff)
        src = "climatology"
    if vals is None:
        return None
    hi = heat_index_c(vals["temp_c"], vals["humidity_pct"])
    return WeatherRow(
        match_num=num, venue=venue, kickoff_utc=kickoff, source=src,
        temp_c=vals["temp_c"], humidity_pct=vals["humidity_pct"],
        wind_kph=vals["wind_kph"], precip_mm=vals["precip_mm"],
        cloud_pct=vals["cloud_pct"], heat_index_c=hi,
    )


def build(max_fixtures: int | None = None, kickoff_hour: int = 19,
          fixtures_path: str = "data/fixtures/wc2026_fixtures.parquet") -> pd.DataFrame:
    fx = pd.read_parquet(fixtures_path).sort_values("num")
    if max_fixtures:
        fx = fx.head(max_fixtures)
    rows: list[WeatherRow] = []
    for _, r in fx.iterrows():
        kickoff = pd.Timestamp(r["date"]).normalize() + pd.Timedelta(hours=kickoff_hour)
        kickoff = kickoff.tz_localize(None)
        row = fetch_for_fixture(int(r["num"]), str(r["venue"]),
                                float(r["lat"]), float(r["lon"]), kickoff)
        if row:
            rows.append(row)
        time.sleep(0.4)
    df = pd.DataFrame([r.__dict__ for r in rows])
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    if len(df):
        df.to_parquet(OUT_PATH, index=False)
    return df


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-fixtures", type=int, default=None)
    ap.add_argument("--kickoff-hour", type=int, default=19)
    args = ap.parse_args()
    df = build(max_fixtures=args.max_fixtures, kickoff_hour=args.kickoff_hour)
    n_fc = int((df["source"] == "forecast").sum()) if len(df) else 0
    n_cl = int((df["source"] == "climatology").sum()) if len(df) else 0
    print(f"wrote {len(df)} rows -> {OUT_PATH}  (forecast={n_fc}, climatology={n_cl})")


if __name__ == "__main__":
    main()
