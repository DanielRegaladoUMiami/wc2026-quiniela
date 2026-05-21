"""Head-to-head model comparison.

Given prediction logs per (tournament, model), compute RPS / log_loss / Brier /
accuracy / ECE and produce a markdown + CSV summary.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.eval.bootstrap import bootstrap_ci
from src.eval.calibration import brier_decomposition, expected_calibration_error
from src.eval.rps import log_loss_1x2, mean_rps


METRIC_COLS = ["n", "rps", "rps_ci_lo", "rps_ci_hi", "log_loss", "brier", "accuracy", "ece"]


def _metrics_for(preds: pd.DataFrame, n_bootstrap: int) -> dict:
    if preds.empty:
        return {c: float("nan") for c in METRIC_COLS} | {"n": 0}
    probs = preds[["p_home", "p_draw", "p_away"]].to_numpy()
    outs = preds["outcome"].astype(int).to_numpy()
    ci = bootstrap_ci(probs, outs, n_resamples=n_bootstrap)
    bd = brier_decomposition(probs, outs)
    return {
        "n": len(preds),
        "rps": mean_rps(probs, outs),
        "rps_ci_lo": ci["ci_lo"],
        "rps_ci_hi": ci["ci_hi"],
        "log_loss": log_loss_1x2(probs, outs),
        "brier": bd.brier,
        "accuracy": float((probs.argmax(axis=1) == outs).mean()),
        "ece": expected_calibration_error(probs, outs),
    }


def build_results_table(
    all_preds: pd.DataFrame, n_bootstrap: int = 1000
) -> pd.DataFrame:
    """all_preds must have cols: tournament, model, p_home, p_draw, p_away, outcome."""
    rows = []
    for (tour, model), g in all_preds.groupby(["tournament", "model"], sort=True):
        m = _metrics_for(g, n_bootstrap=n_bootstrap)
        rows.append({"tournament": tour, "model": model, **m})
    return pd.DataFrame(rows)


def build_reliability_decomposition(all_preds: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (tour, model), g in all_preds.groupby(["tournament", "model"], sort=True):
        if g.empty:
            continue
        probs = g[["p_home", "p_draw", "p_away"]].to_numpy()
        outs = g["outcome"].astype(int).to_numpy()
        bd = brier_decomposition(probs, outs)
        rows.append({"tournament": tour, "model": model, **bd.asdict(), "n": len(g)})
    return pd.DataFrame(rows)


def to_markdown(results: pd.DataFrame) -> str:
    if results.empty:
        return "_No results to report._\n"
    df = results.copy()
    for c in ("rps", "log_loss", "brier", "accuracy", "ece", "rps_ci_lo", "rps_ci_hi"):
        if c in df.columns:
            df[c] = df[c].astype(float).round(4)
    df["rps_95ci"] = df.apply(
        lambda r: f"[{r['rps_ci_lo']:.4f}, {r['rps_ci_hi']:.4f}]"
        if pd.notna(r["rps_ci_lo"])
        else "",
        axis=1,
    )
    cols = ["tournament", "model", "n", "rps", "rps_95ci", "log_loss", "brier", "accuracy", "ece"]
    return df[cols].to_markdown(index=False)
