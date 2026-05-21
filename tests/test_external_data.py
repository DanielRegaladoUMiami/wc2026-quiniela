"""Structural tests for external-data fetchers. Network mocked when libs available."""

from __future__ import annotations

import importlib

import pandas as pd
import pytest

from src.data import enrich_venues, fetch_kalshi_markets, fetch_pinnacle_odds, fetch_weather

HAS_RESPONSES = importlib.util.find_spec("responses") is not None


def test_heat_index_returns_temp_when_low() -> None:
    assert fetch_weather.heat_index_c(20.0, 80.0) == 20.0


def test_heat_index_elevated_high_temp_humidity() -> None:
    hi = fetch_weather.heat_index_c(35.0, 70.0)
    assert hi > 35.0


def test_shin_devig_sums_to_one_and_lt_implied() -> None:
    ph, pd_, pa = fetch_pinnacle_odds.shin_devig(1.80, 3.60, 4.50)
    assert abs(ph + pd_ + pa - 1.0) < 1e-6
    raw = 1 / 1.80 + 1 / 3.60 + 1 / 4.50
    assert raw > 1.0
    assert ph < 1 / 1.80
    assert pa < 1 / 4.50


def test_kalshi_schema_cols_constant() -> None:
    assert "ticker" in fetch_kalshi_markets.SCHEMA_COLS
    assert "snapshot_utc" in fetch_kalshi_markets.SCHEMA_COLS


def test_kalshi_normalize_empty_returns_typed_df() -> None:
    df = fetch_kalshi_markets.normalize([], snapshot_utc="2026-05-21T00:00:00+00:00")
    assert list(df.columns) == fetch_kalshi_markets.SCHEMA_COLS
    assert len(df) == 0


def test_venue_wiki_map_covers_16() -> None:
    assert len(enrich_venues.VENUE_WIKI) == 16


def test_pinnacle_tournaments_present() -> None:
    keys = set(fetch_pinnacle_odds.TOURNAMENTS)
    for k in ("WC18", "WC22", "Euro24", "Copa24", "AFCON23", "NL2223"):
        assert k in keys


def test_pinnacle_parse_html_extracts_rows() -> None:
    html = """
    <html><body><table>
    <tr><td colspan="2">12 June 2026</td></tr>
    <tr><td>20:00</td><td>Mexico - Canada</td><td>2-1</td><td>1.80</td><td>3.60</td><td>4.50</td></tr>
    </table></body></html>
    """
    rows = fetch_pinnacle_odds.parse_results_html(html, "TEST")
    assert len(rows) == 1
    r = rows[0]
    assert r.home_team == "Mexico" and r.away_team == "Canada"
    assert abs(r.p_home_market + r.p_draw_market + r.p_away_market - 1.0) < 1e-6
    assert r.vig_pct > 0


def test_enrich_infobox_parses_minimal_html() -> None:
    html = """
    <html><body><table class="infobox">
      <tr><th>Surface</th><td>Grass</td></tr>
      <tr><th>Field size</th><td>105 m × 68 m</td></tr>
      <tr><th>Opened</th><td>1966</td></tr>
      <tr><th>Owner</th><td>FMF</td></tr>
      <tr><th>Capacity</th><td>87,523</td></tr>
    </table></body></html>
    """
    fields = enrich_venues.parse_infobox(html)
    assert "surface" in fields
    assert "field size" in fields
    assert fields["capacity"].replace(",", "").startswith("87523")


@pytest.mark.skipif(not HAS_RESPONSES, reason="responses lib not installed")
def test_kalshi_events_with_mock() -> None:
    import responses

    with responses.RequestsMock() as rs:
        rs.add(
            responses.GET,
            f"{fetch_kalshi_markets.BASE}/events",
            json={"events": [{"event_ticker": "WORLDCUP-2026-WINNER"}], "cursor": ""},
            status=200,
        )
        events = fetch_kalshi_markets.list_event_tickers("WORLDCUP")
    assert events == ["WORLDCUP-2026-WINNER"]


def test_fetch_for_fixture_skips_when_network_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*a, **kw):
        raise RuntimeError("no net")

    monkeypatch.setattr(fetch_weather, "fetch_forecast", boom)
    monkeypatch.setattr(fetch_weather, "fetch_climatology", lambda *a, **kw: None)
    kickoff = pd.Timestamp("2026-06-11 19:00")
    row = fetch_weather.fetch_for_fixture(1, "mexico_city", 19.30, -99.15, kickoff,
                                          today=pd.Timestamp("2026-06-10"))
    assert row is None
