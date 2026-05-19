"""Teams page — all 48 WC2026 participants as cards with flag, nickname, FIFA rank, predictions."""

from __future__ import annotations

from pathlib import Path

import gradio as gr
import pandas as pd

from web.components import latest_sim_dir, no_sim_banner, read_parquet


def _teams_with_predictions() -> pd.DataFrame:
    meta = read_parquet(Path("data/fixtures/team_metadata.parquet"))
    sim = latest_sim_dir()
    if sim is None:
        meta["p_advance_group"] = None
        meta["p_R16_win"] = None
        meta["p_QF_win"] = None
        meta["p_SF_win"] = None
        meta["p_final_win"] = None
        meta["p_champion"] = None
        return meta
    adv = read_parquet(sim / "advancement.parquet")
    df = meta.merge(adv, on="team", how="left")
    return df


def _render_cards(df: pd.DataFrame, conf_filter: str = "All") -> str:
    """Return HTML for the team cards grid."""
    if conf_filter != "All":
        df = df[df["conf"] == conf_filter]
    df = df.sort_values("p_champion", ascending=False, na_position="last").reset_index(drop=True)
    cards = []
    for _, r in df.iterrows():
        flag = r.get("flag_url") or ""
        team = r.get("team", "—")
        nick = r.get("nickname", "")
        rank = r.get("fifa_rank")
        conf = r.get("conf", "")
        best = r.get("best_wc", "")
        p_ch = r.get("p_champion")
        p_adv = r.get("p_advance_group")
        p_ch_pct = f"{p_ch*100:.1f}%" if pd.notna(p_ch) else "—"
        p_adv_pct = f"{p_adv*100:.0f}%" if pd.notna(p_adv) else "—"
        rank_str = f"#{int(rank)}" if pd.notna(rank) else "—"
        cards.append(f"""
<div style="background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%); border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.04); transition: transform 0.15s, box-shadow 0.15s;" onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(0,0,0,0.08)';" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 1px 3px rgba(0,0,0,0.04)';">
  <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
    <img src="{flag}" alt="{team} flag" style="width: 48px; height: 32px; object-fit: cover; border-radius: 4px; border: 1px solid #cbd5e1;" loading="lazy"/>
    <div style="flex: 1; min-width: 0;">
      <div style="font-weight: 700; font-size: 15px; color: #0f172a; line-height: 1.2;">{team}</div>
      <div style="font-size: 11px; color: #64748b; font-style: italic;">{nick}</div>
    </div>
    <div style="font-weight: 700; font-size: 13px; color: #16a34a; background: #dcfce7; padding: 4px 8px; border-radius: 6px;">{rank_str}</div>
  </div>
  <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 12px;">
    <div style="background: #f1f5f9; padding: 6px 8px; border-radius: 6px;">
      <div style="color: #64748b; font-size: 10px; text-transform: uppercase; letter-spacing: 0.5px;">Conf</div>
      <div style="color: #0f172a; font-weight: 600;">{conf}</div>
    </div>
    <div style="background: #f1f5f9; padding: 6px 8px; border-radius: 6px;">
      <div style="color: #64748b; font-size: 10px; text-transform: uppercase; letter-spacing: 0.5px;">Best WC</div>
      <div style="color: #0f172a; font-weight: 600; font-size: 11px;">{best}</div>
    </div>
    <div style="background: #fef3c7; padding: 6px 8px; border-radius: 6px;">
      <div style="color: #92400e; font-size: 10px; text-transform: uppercase; letter-spacing: 0.5px;">P(advance)</div>
      <div style="color: #78350f; font-weight: 700;">{p_adv_pct}</div>
    </div>
    <div style="background: #ede9fe; padding: 6px 8px; border-radius: 6px;">
      <div style="color: #5b21b6; font-size: 10px; text-transform: uppercase; letter-spacing: 0.5px;">P(champion)</div>
      <div style="color: #4c1d95; font-weight: 700;">{p_ch_pct}</div>
    </div>
  </div>
</div>
""")
    grid = "".join(cards)
    return f"""
<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; padding: 8px 0;">
{grid}
</div>
"""


def build_page() -> None:
    df = _teams_with_predictions()
    if latest_sim_dir() is None:
        gr.Markdown(no_sim_banner())
    gr.Markdown("# Equipos · WC 2026 · 48 selecciones")
    gr.Markdown(
        "Sorted by **P(champion)** from our 5k Monte Carlo simulation (DC + LightGBM + "
        "Bayesian blend). Click a confederation chip to filter."
    )
    confs = ["All"] + sorted(df["conf"].dropna().unique().tolist())
    with gr.Row():
        conf_picker = gr.Radio(choices=confs, value="All", label="Confederation", interactive=True)
    cards_html = gr.HTML(_render_cards(df, "All"))

    def update(c):
        return _render_cards(df, c)

    conf_picker.change(update, inputs=[conf_picker], outputs=[cards_html])
