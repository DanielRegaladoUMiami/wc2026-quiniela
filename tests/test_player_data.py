"""Structural tests for the player-data pipeline. No network calls."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

WIKI = Path("data/raw/squads/wiki_squads.parquet")
FBREF = Path("data/raw/fbref/intl_player_stats.parquet")
TM = Path("data/raw/transfermarkt/squads.parquet")
PHOTOS = Path("data/raw/photos/manifest.parquet")
PLAYERS = Path("data/processed/players.parquet")
TEAM_STATS = Path("data/processed/team_stats.parquet")
META = Path("data/fixtures/team_metadata.parquet")


@pytest.mark.skipif(not WIKI.exists(), reason="run fetch_wiki_squads first")
def test_wiki_squads_schema():
    df = pd.read_parquet(WIKI)
    assert {
        "team",
        "player_name",
        "position",
        "dob",
        "club",
        "caps",
        "goals",
        "shirt_number",
        "source_url",
    }.issubset(df.columns)
    assert df["team"].notna().all()
    assert df["player_name"].notna().all()
    assert len(df) > 500


@pytest.mark.skipif(not FBREF.exists(), reason="run fetch_fbref_intl first")
def test_fbref_intl_schema():
    df = pd.read_parquet(FBREF)
    assert "team" in df.columns
    assert "player" in df.columns or "player_name" in df.columns
    assert len(df) > 0


@pytest.mark.skipif(not TM.exists(), reason="run fetch_transfermarkt first")
def test_tm_schema():
    df = pd.read_parquet(TM)
    expected = {"team", "tm_id", "player_name", "market_value_eur"}
    assert expected.issubset(df.columns)


@pytest.mark.skipif(not PHOTOS.exists(), reason="run fetch_player_photos first")
def test_photos_schema():
    df = pd.read_parquet(PHOTOS)
    assert {"team", "player_name", "wikidata_id", "image_url"}.issubset(df.columns)


@pytest.mark.skipif(not PLAYERS.exists(), reason="run build_player_table first")
def test_players_processed():
    df = pd.read_parquet(PLAYERS)
    expected = {
        "team",
        "fifa_code",
        "player_name",
        "position",
        "age",
        "dob",
        "club",
        "caps",
        "goals",
        "intl_xg",
        "intl_goals_per_match",
        "market_value_eur",
        "contract_until",
        "photo_url",
        "shirt_number",
    }
    assert expected.issubset(df.columns)
    assert df["team"].notna().all()
    assert df["player_name"].notna().all()
    assert df["team"].nunique() == 48
    # Dedup contract
    assert df.duplicated(subset=["team", "player_name"]).sum() == 0


@pytest.mark.skipif(not TEAM_STATS.exists(), reason="run build_team_stats first")
def test_team_stats():
    df = pd.read_parquet(TEAM_STATS)
    assert len(df) == 48
    assert {
        "avg_age",
        "median_age",
        "squad_market_value_eur_total",
        "squad_market_value_top11",
        "n_top5_league_players",
        "manager_name",
        "manager_tenure_days",
    }.issubset(df.columns)
    # Joined with team_metadata
    assert {"fifa_code", "fifa_rank", "conf"}.issubset(df.columns)


def test_team_metadata_has_48():
    df = pd.read_parquet(META)
    assert len(df) == 48
