"""FIFA World Cup 2026 — Gradio dashboard."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import gradio as gr

from web.pages import about, bracket, home, methodology, model_vs_market, picks, standings

THEME = gr.themes.Soft(
    primary_hue="green",
    secondary_hue="orange",
    neutral_hue="slate",
    font=[gr.themes.GoogleFont("Inter"), "system-ui", "sans-serif"],
)

CSS = """
.gradio-container { max-width: 1280px !important; }
h1 { letter-spacing: -0.5px; }
footer { display: none !important; }
"""


def build_app() -> gr.Blocks:
    with gr.Blocks(title="WC2026 Quiniela") as demo:
        with gr.Tabs():
            with gr.Tab("Home"):
                home.build_page()
            with gr.Tab("Bracket"):
                bracket.build_page()
            with gr.Tab("Standings"):
                standings.build_page()
            with gr.Tab("Model vs Market"):
                model_vs_market.build_page()
            with gr.Tab("Quiniela Picks"):
                picks.build_page()
            with gr.Tab("Methodology"):
                methodology.build_page()
            with gr.Tab("About"):
                about.build_page()
    return demo


demo = build_app()

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, theme=THEME, css=CSS)
