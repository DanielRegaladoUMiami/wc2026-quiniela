from __future__ import annotations

import gradio as gr
import pandas as pd

from web.components import fixtures, match_probs, no_sim_banner


def _confidence_color(p: float) -> str:
    if p >= 0.55:
        return "#1b8a3a"  # green
    if p >= 0.40:
        return "#d4a017"  # yellow
    return "#c0392b"  # red


def _1x2_table(rows: pd.DataFrame) -> pd.DataFrame:
    picks, conf = [], []
    for r in rows.itertuples():
        triples = [
            ("1 " + r.home, r.p_home_win),
            ("X Draw", r.p_draw),
            ("2 " + r.away, r.p_away_win),
        ]
        pick, p = max(triples, key=lambda x: x[1])
        picks.append(pick)
        conf.append(p)
    return pd.DataFrame(
        {
            "Match #": rows["num"].values,
            "Date": pd.to_datetime(rows["date"]).dt.strftime("%a %b %d").values,
            "Match": [f"{r.home} vs {r.away}" for r in rows.itertuples()],
            "Pick": picks,
            "Confidence": [f"{p:.0%}" for p in conf],
            "Tier": ["High" if p >= 0.55 else ("Med" if p >= 0.40 else "Low") for p in conf],
        }
    )


def _exact_table(rows: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Match #": rows["num"].values,
            "Match": [f"{r.home} vs {r.away}" for r in rows.itertuples()],
            "xG home": rows["expected_home_goals"].round(2).values,
            "xG away": rows["expected_away_goals"].round(2).values,
            "Pick (mode)": [
                f"{round(r.expected_home_goals)}-{round(r.expected_away_goals)}"
                for r in rows.itertuples()
            ],
        }
    )


def _bracket_table(adv_like_rows: pd.DataFrame) -> pd.DataFrame:
    return adv_like_rows.head(8)


def build_page() -> None:
    gr.Markdown("# Quiniela Picks")
    gr.Markdown(
        "> **Contrarian strategy**: in pool play, public money concentrates on Brazil/France/Argentina "
        "and on home favorites. Our entries skew slightly toward calibrated dark horses "
        "(e.g. Spain, Portugal, Netherlands when our P(champion) > market). "
        "Expected pool finish: top-decile if at least one mid-favorite hits, median otherwise."
    )

    mp = match_probs()
    if mp is None:
        gr.Markdown(no_sim_banner())
        return
    fx = fixtures()
    merged = fx.merge(mp, on=["num", "home", "away"], how="left").dropna(subset=["p_home_win"])
    group_only = merged[merged["stage"] == "group"].sort_values("num")

    with gr.Tabs():
        with gr.Tab("1X2 (FIFA Quiniela MX)"):
            gr.Dataframe(_1x2_table(group_only), interactive=False, wrap=True)
        with gr.Tab("Exact Score"):
            gr.Dataframe(_exact_table(group_only), interactive=False, wrap=True)
        with gr.Tab("Bracket"):
            from web.components import advancement

            adv = advancement()
            if adv is None:
                gr.Markdown(no_sim_banner())
            else:
                top = adv.sort_values("p_champion", ascending=False).head(8).copy()
                top["P(Champion)"] = (top["p_champion"] * 100).round(1)
                gr.Markdown("**Top 8 champion picks** (use for bracket-style entry):")
                gr.Dataframe(
                    top[["team", "P(Champion)"]].rename(columns={"team": "Team"}), interactive=False
                )
