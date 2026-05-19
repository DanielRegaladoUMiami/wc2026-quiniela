from __future__ import annotations

import gradio as gr
import plotly.graph_objects as go

from web.components import PALETTE, ROOT


def _pipeline_fig() -> go.Figure:
    nodes = [
        "Data\n(FBref / Elo / Kalshi)",
        "Feature engineering",
        "Dixon-Coles",
        "Hierarchical Bayesian",
        "LightGBM",
        "Market features",
        "Stacker + isotonic",
        "Monte Carlo (50k sims)",
        "Strategy / Quiniela",
    ]
    x = [0.02, 0.18, 0.40, 0.40, 0.40, 0.40, 0.62, 0.80, 0.96]
    y = [0.50, 0.50, 0.85, 0.65, 0.45, 0.25, 0.50, 0.50, 0.50]
    edges = [(0, 1), (1, 2), (1, 3), (1, 4), (1, 5),
             (2, 6), (3, 6), (4, 6), (5, 6), (6, 7), (7, 8)]
    fig = go.Figure()
    for a, b in edges:
        fig.add_shape(type="line", x0=x[a], y0=y[a], x1=x[b], y1=y[b],
                      line=dict(color=PALETTE["muted"], width=1.5))
    fig.add_scatter(
        x=x, y=y, mode="markers+text", text=nodes, textposition="middle center",
        marker=dict(size=110, color=PALETTE["primary"], line=dict(color="white", width=2)),
        textfont=dict(color="white", size=10), hoverinfo="text",
    )
    fig.update_layout(
        template="plotly_white", height=380, showlegend=False,
        xaxis=dict(visible=False, range=[-0.05, 1.05]),
        yaxis=dict(visible=False, range=[0, 1]),
        margin=dict(l=10, r=10, t=20, b=10),
    )
    return fig


def build_page() -> None:
    gr.Markdown("# Methodology")
    gr.Plot(_pipeline_fig())
    md_path = ROOT / "METHODOLOGY.md"
    text = md_path.read_text() if md_path.exists() else "METHODOLOGY.md not found."
    gr.Markdown(text)
