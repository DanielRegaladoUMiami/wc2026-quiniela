"""Validate the unified match log structure and basic sanity invariants."""

from pathlib import Path

import polars as pl
import pytest

from src.data.build_match_log import CANONICAL_COLS

MATCH_LOG = Path("data/processed/matches.parquet")

pytestmark = pytest.mark.skipif(
    not MATCH_LOG.exists(),
    reason="Run `make data` to build the match log first.",
)


@pytest.fixture(scope="module")
def matches() -> pl.DataFrame:
    return pl.read_parquet(MATCH_LOG)


def test_canonical_schema(matches: pl.DataFrame) -> None:
    assert list(matches.columns) == CANONICAL_COLS


def test_match_ids_unique(matches: pl.DataFrame) -> None:
    assert matches["match_id"].n_unique() == len(matches)


def test_dates_sorted_and_in_range(matches: pl.DataFrame) -> None:
    dates = matches["date"]
    assert dates.min().year >= 1872
    assert dates.max().year <= 2030


def test_no_negative_goals(matches: pl.DataFrame) -> None:
    assert matches.filter(pl.col("home_goals") < 0).is_empty()
    assert matches.filter(pl.col("away_goals") < 0).is_empty()


def test_wc_2022_present(matches: pl.DataFrame) -> None:
    """Sanity: the canonical Kaggle dataset must contain the 2022 World Cup final."""
    final = matches.filter(
        (pl.col("date") == pl.lit("2022-12-18").str.strptime(pl.Date, "%Y-%m-%d"))
        & (pl.col("competition").str.contains("World Cup"))
    )
    assert len(final) == 1
    row = final.row(0, named=True)
    assert {row["home_team"], row["away_team"]} == {"Argentina", "France"}
