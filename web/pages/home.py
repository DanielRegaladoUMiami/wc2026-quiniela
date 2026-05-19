from __future__ import annotations

from datetime import date

import gradio as gr
import pandas as pd
import plotly.graph_objects as go

from web.components import (
    PALETTE,
    TOURNAMENT_START,
    fixtures,
    match_probs,
    no_sim_banner,
    sim_timestamp,
)


def _bar_fig(rows: pd.DataFrame) -> go.Figure:
    labels = [f"{r.home} vs {r.away}<br><sub>{r.date_str} • {r.venue}</sub>"
              for r in rows.itertuples()]
    fig = go.Figure()
    fig.add_bar(name="Home", y=labels, x=rows.p_home_win, orientation="h",
                marker_color=PALETTE["home"],
                hovertemplate="%{y}<br>P(home win)=%{x:.1%}<extra></extra>")
    fig.add_bar(name="Draw", y=labels, x=rows.p_draw, orientation="h",
                marker_color=PALETTE["draw"],
                hovertemplate="%{y}<br>P(draw)=%{x:.1%}<extra></extra>")
    fig.add_bar(name="Away", y=labels, x=rows.p_away_win, orientation="h",
                marker_color=PALETTE["away"],
                hovertemplate="%{y}<br>P(away win)=%{x:.1%}<extra></extra>")
    fig.update_layout(
        barmode="stack", template="plotly_white",
        height=80 + 70 * len(rows), margin=dict(l=10, r=10, t=30, b=10),
        legend=dict(orientation="h", y=1.08, x=0.5, xanchor="center"),
        xaxis=dict(tickformat=".0%", range=[0, 1], showgrid=False),
        yaxis=dict(showgrid=False, autorange="reversed"),
    )
    return fig


def _picks_table(rows: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame({
        "Match": [f"{r.home} vs {r.away}" for r in rows.itertuples()],
        "Date": rows.date_str.values,
        "Venue": rows.venue.values,
        "1X2 pick": [
            ("Home " + r.home) if r.p_home_win == max(r.p_home_win, r.p_draw, r.p_away_win)
            else ("Draw" if r.p_draw >= r.p_away_win else f"Away {r.away}")
            for r in rows.itertuples()
        ],
        "Confidence": [f"{max(r.p_home_win, r.p_draw, r.p_away_win):.0%}" for r in rows.itertuples()],
        "Exact score": [
            f"{round(r.expected_home_goals)}-{round(r.expected_away_goals)}"
            for r in rows.itertuples()
        ],
        "xG": [f"{r.expected_home_goals:.2f} – {r.expected_away_goals:.2f}" for r in rows.itertuples()],
    })
    return out


def build_page() -> None:
    today = date.today()
    days_to = (TOURNAMENT_START - today).days
    countdown = (f"Tournament starts in **{days_to} days** "
                 f"({TOURNAMENT_START.isoformat()})") if days_to > 0 else "**Tournament live**"

    gr.Markdown(
        f"""
        # FIFA World Cup 2026 — Live Predictions
        Probabilistic model | Last sim run: **{sim_timestamp()}** | {countdown}
        """
    )

    mp = match_probs()
    if mp is None:
        gr.Markdown(no_sim_banner())
        return

    fx = fixtures().copy()
    fx["date_str"] = pd.to_datetime(fx["date"]).dt.strftime("%a %b %d")
    merged = fx.merge(mp, on=["num", "home", "away"], how="left")
    merged = merged.dropna(subset=["p_home_win"])

    today_ts = pd.Timestamp(today)
    upcoming = merged[pd.to_datetime(merged["date"]) >= today_ts].sort_values("date")
    if upcoming.empty:
        upcoming = merged.sort_values("date")
    rows = upcoming.head(5 if days_to <= 0 else 4 if days_to > 0 else 5).reset_index(drop=True)
    if days_to > 0:
        opener_date = pd.to_datetime(merged["date"]).min()
        openers = merged[pd.to_datetime(merged["date"]) == opener_date]
        rows = openers.head(5).reset_index(drop=True) if len(openers) else rows

    gr.Markdown("### Opening matches" if days_to > 0 else "### Next 5 matches")
    gr.Plot(_bar_fig(rows))
    gr.Markdown("### Recommended picks")
    gr.Dataframe(_picks_table(rows), interactive=False, wrap=True)
