from __future__ import annotations

import gradio as gr
import pandas as pd
import plotly.graph_objects as go

from web.components import PALETTE, advancement, groups, no_sim_banner

STAGES = [
    ("p_R32_win", "R16"),
    ("p_R16_win", "QF"),
    ("p_QF_win", "SF"),
    ("p_SF_win", "Final"),
    ("p_final_win", "Champion"),
]


def _treemap(adv: pd.DataFrame) -> go.Figure:
    top = adv.sort_values("p_champion", ascending=False).head(16)
    fig = go.Figure(go.Treemap(
        labels=top["team"],
        parents=[""] * len(top),
        values=top["p_champion"],
        marker=dict(colorscale="Greens", line=dict(color="white", width=1)),
        hovertemplate="<b>%{label}</b><br>P(champion)=%{value:.1%}<extra></extra>",
        textinfo="label+value", texttemplate="<b>%{label}</b><br>%{value:.1%}",
    ))
    fig.update_layout(template="plotly_white", height=460, margin=dict(l=8, r=8, t=30, b=8))
    return fig


def _sankey(adv: pd.DataFrame) -> go.Figure:
    top = adv.sort_values("p_champion", ascending=False).head(16).reset_index(drop=True)
    stage_labels = ["R16", "QF", "SF", "Final", "Champion"]
    labels = list(top["team"]) + stage_labels
    team_idx = {t: i for i, t in enumerate(top["team"])}
    stage_idx = {s: len(top) + i for i, s in enumerate(stage_labels)}
    src, tgt, val = [], [], []
    cols = ["p_R32_win", "p_R16_win", "p_QF_win", "p_SF_win", "p_final_win"]
    for _, r in top.iterrows():
        prev = team_idx[r["team"]]
        for c, s in zip(cols, stage_labels):
            src.append(prev); tgt.append(stage_idx[s]); val.append(max(r[c], 0.001))
            prev = stage_idx[s]
    fig = go.Figure(go.Sankey(
        node=dict(label=labels, pad=12, thickness=14,
                  color=[PALETTE["primary"]] * len(top) + [PALETTE["accent"]] * len(stage_labels)),
        link=dict(source=src, target=tgt, value=val,
                  hovertemplate="P=%{value:.1%}<extra></extra>"),
    ))
    fig.update_layout(template="plotly_white", height=520, margin=dict(l=8, r=8, t=30, b=8))
    return fig


def _table(adv: pd.DataFrame, grp: pd.DataFrame) -> pd.DataFrame:
    t = adv.merge(grp, on="team", how="left")
    t = t.sort_values("p_champion", ascending=False)
    out = pd.DataFrame({
        "Team": t["team"],
        "Group": t["group"],
        "P(advance)": (t["p_advance_group"] * 100).round(1),
        "P(R16)": (t["p_R32_win"] * 100).round(1),
        "P(QF)": (t["p_R16_win"] * 100).round(1),
        "P(SF)": (t["p_QF_win"] * 100).round(1),
        "P(Final)": (t["p_SF_win"] * 100).round(1),
        "P(Champion)": (t["p_final_win"] * 100).round(1),
    })
    return out


def build_page() -> None:
    gr.Markdown("# Bracket Probabilities")
    adv = advancement()
    if adv is None:
        gr.Markdown(no_sim_banner()); return
    grp = groups()
    with gr.Tabs():
        with gr.Tab("Sankey (top 16)"):
            gr.Plot(_sankey(adv))
        with gr.Tab("Treemap (champion)"):
            gr.Plot(_treemap(adv))
    gr.Markdown("### All 48 teams")
    df = _table(adv, grp)
    search = gr.Textbox(label="Filter team", placeholder="e.g. Mexico", scale=1)
    table = gr.Dataframe(df, interactive=False, wrap=True)

    def _filter(q: str) -> pd.DataFrame:
        if not q:
            return df
        return df[df["Team"].str.contains(q, case=False, na=False)]

    search.change(_filter, search, table)
