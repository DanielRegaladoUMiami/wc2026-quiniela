from __future__ import annotations

import gradio as gr
import pandas as pd
import plotly.graph_objects as go

from web.components import PALETTE, advancement, groups, no_sim_banner


def _group_fig(letter: str, rows: pd.DataFrame) -> go.Figure:
    rows = rows.sort_values("p_advance_group", ascending=True)
    fig = go.Figure()
    fig.add_bar(
        y=rows["team"],
        x=rows["p_advance_group"],
        orientation="h",
        marker_color=PALETTE["primary"],
        hovertemplate="%{y}<br>P(advance)=%{x:.1%}<extra></extra>",
        text=[f"{v:.0%}" for v in rows["p_advance_group"]],
        textposition="inside",
        insidetextfont=dict(color="white"),
    )
    fig.update_layout(
        title=f"Group {letter}",
        template="plotly_white",
        height=220,
        margin=dict(l=8, r=8, t=40, b=8),
        xaxis=dict(range=[0, 1], tickformat=".0%", showgrid=False, visible=False),
        yaxis=dict(showgrid=False),
        showlegend=False,
    )
    return fig


def build_page() -> None:
    gr.Markdown("# Standings & Group probabilities")
    adv = advancement()
    if adv is None:
        gr.Markdown(no_sim_banner())
        return
    grp = groups().merge(adv, on="team", how="left")
    letters = sorted(grp["group"].dropna().unique())
    for i in range(0, len(letters), 4):
        with gr.Row():
            for L in letters[i : i + 4]:
                with gr.Column():
                    gr.Plot(_group_fig(L, grp[grp["group"] == L]))
