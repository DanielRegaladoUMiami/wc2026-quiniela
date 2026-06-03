"""Snapshot Kalshi WC2026 markets via public read-only API.

Endpoints (no auth required for public data):
  GET https://api.elections.kalshi.com/trade-api/v2/events?series_ticker=WORLDCUP
  GET https://api.elections.kalshi.com/trade-api/v2/markets?event_ticker=...

Persists one parquet per run at data/raw/kalshi/markets_snapshot_YYYYMMDD.parquet.
Empty results are tolerated (writes a zero-row file with the right schema).
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

BASE = "https://api.elections.kalshi.com/trade-api/v2"
OUT_DIR = Path("data/raw/kalshi")
HEADERS = {"User-Agent": "wc2026-quiniela/0.1 (github.com/DanielRegaladoUMiami/wc2026-quiniela)"}

SCHEMA_COLS = [
    "ticker",
    "event_ticker",
    "series_ticker",
    "title",
    "subtitle",
    "status",
    "yes_bid",
    "yes_ask",
    "no_bid",
    "no_ask",
    "last_price",
    "volume",
    "open_interest",
    "open_time",
    "close_time",
    "expected_expiration_time",
    "snapshot_utc",
]


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=2, max=20))
def _get(path: str, params: dict | None = None) -> dict:
    r = requests.get(f"{BASE}{path}", params=params or {}, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()


def list_event_tickers(prefix: str = "WORLDCUP") -> list[str]:
    """Find WC2026-relevant events. Kalshi groups markets by event_ticker."""
    events: list[str] = []
    cursor: str | None = None
    for _ in range(20):
        params = {"limit": 200, "status": "open"}
        if cursor:
            params["cursor"] = cursor
        try:
            payload = _get("/events", params=params)
        except Exception as e:
            print(f"events fetch failed: {e}")
            return events
        for ev in payload.get("events", []):
            tk = ev.get("event_ticker", "")
            if (
                prefix.upper() in tk.upper()
                or "WORLD-CUP" in tk.upper()
                or "WORLDCUP" in tk.upper()
            ):
                events.append(tk)
        cursor = payload.get("cursor") or None
        if not cursor:
            break
    return sorted(set(events))


def fetch_markets_for_event(event_ticker: str) -> list[dict]:
    cursor: str | None = None
    out: list[dict] = []
    for _ in range(20):
        params = {"event_ticker": event_ticker, "limit": 200}
        if cursor:
            params["cursor"] = cursor
        try:
            payload = _get("/markets", params=params)
        except Exception as e:
            print(f"markets fetch failed for {event_ticker}: {e}")
            break
        out.extend(payload.get("markets", []))
        cursor = payload.get("cursor") or None
        if not cursor:
            break
    return out


def normalize(markets: list[dict], snapshot_utc: str) -> pd.DataFrame:
    rows = []
    for m in markets:
        rows.append(
            {
                "ticker": m.get("ticker"),
                "event_ticker": m.get("event_ticker"),
                "series_ticker": m.get("series_ticker"),
                "title": m.get("title"),
                "subtitle": m.get("subtitle"),
                "status": m.get("status"),
                "yes_bid": m.get("yes_bid"),
                "yes_ask": m.get("yes_ask"),
                "no_bid": m.get("no_bid"),
                "no_ask": m.get("no_ask"),
                "last_price": m.get("last_price"),
                "volume": m.get("volume"),
                "open_interest": m.get("open_interest"),
                "open_time": m.get("open_time"),
                "close_time": m.get("close_time"),
                "expected_expiration_time": m.get("expected_expiration_time"),
                "snapshot_utc": snapshot_utc,
            }
        )
    if not rows:
        return pd.DataFrame(columns=SCHEMA_COLS)
    return pd.DataFrame(rows)[SCHEMA_COLS]


def build() -> pd.DataFrame:
    snapshot = datetime.now(UTC).isoformat()
    stamp = datetime.now(UTC).strftime("%Y%m%d")
    events = list_event_tickers("WORLDCUP")
    all_markets: list[dict] = []
    for ev in events:
        all_markets.extend(fetch_markets_for_event(ev))
    df = normalize(all_markets, snapshot)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"markets_snapshot_{stamp}.parquet"
    df.to_parquet(out, index=False)
    print(f"events={len(events)}  markets={len(df)}  -> {out}")
    return df


def main() -> None:
    build()


if __name__ == "__main__":
    main()
