"""Shared helpers for the WC2026 Gradio dashboard."""

from __future__ import annotations

import functools
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"

PALETTE = {
    "primary": "#0B3D2E",
    "accent": "#F26B1F",
    "blue": "#11366B",
    "home": "#0B7A3D",
    "draw": "#C0C0C0",
    "away": "#F26B1F",
    "muted": "#5A6B73",
    "bg": "#FFFFFF",
}

TOURNAMENT_START = date(2026, 6, 11)


def _mtime(p: Path) -> float:
    try:
        return p.stat().st_mtime
    except FileNotFoundError:
        return 0.0


@functools.lru_cache(maxsize=8)
def _read_parquet_cached(path_str: str, _mtime_key: float) -> pd.DataFrame:
    return pd.read_parquet(path_str)


def read_parquet(p: Path) -> pd.DataFrame:
    return _read_parquet_cached(str(p), _mtime(p))


def latest_sim_dir() -> Path | None:
    sims = sorted((DATA / "sims").glob("sim_run_*"))
    return sims[-1] if sims else None


def fixtures() -> pd.DataFrame:
    return read_parquet(DATA / "fixtures" / "wc2026_fixtures.parquet")


def groups() -> pd.DataFrame:
    return read_parquet(DATA / "fixtures" / "groups.parquet")


def venues() -> pd.DataFrame:
    return read_parquet(DATA / "fixtures" / "venues.parquet")


def advancement() -> pd.DataFrame | None:
    d = latest_sim_dir()
    return read_parquet(d / "advancement.parquet") if d else None


def match_probs() -> pd.DataFrame | None:
    d = latest_sim_dir()
    return read_parquet(d / "match_probs.parquet") if d else None


def sample_brackets() -> pd.DataFrame | None:
    d = latest_sim_dir()
    return read_parquet(d / "sample_brackets.parquet") if d else None


def elo_history() -> pd.DataFrame:
    return read_parquet(DATA / "processed" / "elo_ratings_history.parquet")


def backtest(name: str) -> pd.DataFrame | None:
    p = DATA / "sims" / f"backtest_gbm_{name}.parquet"
    return read_parquet(p) if p.exists() else None


def sim_timestamp() -> str:
    d = latest_sim_dir()
    if not d:
        return "n/a"
    ts = d.name.replace("sim_run_", "")
    return f"{ts[:4]}-{ts[4:6]}-{ts[6:8]} {ts[8:10]}:{ts[10:12]} UTC"


def no_sim_banner() -> str:
    return (
        "## Predictions not generated yet\n\n"
        "Run `make sim` to populate `data/sims/sim_run_*/`. "
        "The dashboard will hot-reload once parquet files appear."
    )
