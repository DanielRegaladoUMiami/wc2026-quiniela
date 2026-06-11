from __future__ import annotations

import gradio as gr
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from web.components import PALETTE, backtest


def _rps_row(p_home: float, p_draw: float, p_away: float, outcome: int) -> float:
    o = np.zeros(3)
    o[int(outcome)] = 1.0
    p = np.array([p_home, p_draw, p_away])
    c_p = np.cumsum(p)
    c_o = np.cumsum(o)
    return float(np.mean((c_p - c_o) ** 2))


def _logloss_row(p_home: float, p_draw: float, p_away: float, outcome: int) -> float:
    p = max(min([p_home, p_draw, p_away][int(outcome)], 1 - 1e-12), 1e-12)
    return -float(np.log(p))


def _enrich(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["rps"] = [_rps_row(r.p_home, r.p_draw, r.p_away, r.outcome) for r in df.itertuples()]
    df["ll"] = [_logloss_row(r.p_home, r.p_draw, r.p_away, r.outcome) for r in df.itertuples()]
    df["cum_ll"] = df["ll"].cumsum() / (np.arange(len(df)) + 1)
    return df


def _line(wc22: pd.DataFrame | None, eu24: pd.DataFrame | None) -> go.Figure:
    fig = go.Figure()
    if wc22 is not None:
        d = _enrich(wc22)
        fig.add_scatter(
            x=list(range(1, len(d) + 1)),
            y=d["cum_ll"],
            mode="lines+markers",
            name="WC 2022",
            line=dict(color=PALETTE["primary"], width=2),
        )
    if eu24 is not None:
        d = _enrich(eu24)
        fig.add_scatter(
            x=list(range(1, len(d) + 1)),
            y=d["cum_ll"],
            mode="lines+markers",
            name="Euro 2024",
            line=dict(color=PALETTE["accent"], width=2),
        )
    fig.add_hline(
        y=0.21,
        line_dash="dash",
        line_color=PALETTE["muted"],
        annotation_text="Bookmaker closing ≈ 0.21 RPS",
        annotation_position="top right",
    )
    fig.update_layout(
        template="plotly_white",
        height=420,
        title="Cumulative log-loss across backtests (lower is better)",
        xaxis_title="Match #",
        yaxis_title="Mean log-loss",
        margin=dict(l=10, r=10, t=50, b=10),
    )
    return fig


def build_page() -> None:
    gr.Markdown("# Model vs Market")
    wc22 = backtest("wc2022")
    eu24 = backtest("euro2024")
    gr.Plot(_line(wc22, eu24))

    parts = []
    for name, df in [("WC2022", wc22), ("Euro2024", eu24)]:
        if df is None:
            continue
        d = _enrich(df)
        parts.append(f"**{name}** RPS: {d['rps'].mean():.3f} | LogLoss: {d['ll'].mean():.3f}")
    parts.append("Target: **RPS < 0.21** (≈ bookmaker closing line).")
    gr.Markdown("Our backtest: " + " · ".join(parts))
