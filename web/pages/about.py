from __future__ import annotations

import gradio as gr


def build_page() -> None:
    gr.Markdown(
        """
        # About

        **Author** — Daniel Regalado, MS Business Analytics, University of Miami.
        Bilingual ES/EN. Cuban. ML systems for sports prediction and pool optimization.

        **Repo** — <https://github.com/DanielRegaladoUMiami/wc2026-quiniela>
        **License** — Apache 2.0

        **Stack** — Dixon-Coles · Hierarchical Bayesian (PyMC) · LightGBM · Kalshi market features ·
        Stacker w/ isotonic calibration · Monte Carlo bracket sims.

        ---

        > *All models are wrong; some are useful.* — George Box

        **Disclaimer** — Predictions are probabilistic. Not financial advice.
        Use for entertainment / academic interest only.
        """
    )
