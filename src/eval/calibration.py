"""Reliability diagrams + Brier decomposition for 1X2 forecasts.

For 1X2 we flatten the (N, 3) probability matrix and (N, 3) one-hot outcomes into
3N pairs and build a single reliability curve per model. This is the
"all-outcomes-pooled" convention (Bröcker & Smith 2007); it gives a clean
single-figure-of-merit ECE.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd


DEFAULT_BINS = np.linspace(0.0, 1.0, 11)  # 10 bins of width 0.1


def _pool_probs_outcomes(probs: np.ndarray, outcomes: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    n, k = probs.shape
    one_hot = np.zeros_like(probs)
    one_hot[np.arange(n), outcomes.astype(int)] = 1.0
    return probs.ravel(), one_hot.ravel()


def reliability_table(
    probs: np.ndarray, outcomes: np.ndarray, bins: np.ndarray = DEFAULT_BINS
) -> pd.DataFrame:
    """Per-bin: bin_lo, bin_hi, bin_mid, n, mean_predicted, observed_frequency."""
    p, o = _pool_probs_outcomes(np.asarray(probs), np.asarray(outcomes))
    # np.digitize: index 0..len(bins) — clip to bin indices 1..len(bins)-1
    idx = np.clip(np.digitize(p, bins, right=False) - 1, 0, len(bins) - 2)
    rows = []
    for b in range(len(bins) - 1):
        mask = idx == b
        n = int(mask.sum())
        rows.append(
            {
                "bin_lo": float(bins[b]),
                "bin_hi": float(bins[b + 1]),
                "bin_mid": float(0.5 * (bins[b] + bins[b + 1])),
                "n": n,
                "mean_predicted": float(p[mask].mean()) if n else np.nan,
                "observed_frequency": float(o[mask].mean()) if n else np.nan,
            }
        )
    return pd.DataFrame(rows)


def expected_calibration_error(
    probs: np.ndarray, outcomes: np.ndarray, bins: np.ndarray = DEFAULT_BINS
) -> float:
    """ECE = sum_b (n_b / N) * |obs_b - pred_b|."""
    tbl = reliability_table(probs, outcomes, bins)
    total = tbl["n"].sum()
    if total == 0:
        return float("nan")
    w = tbl["n"] / total
    diffs = (tbl["observed_frequency"] - tbl["mean_predicted"]).abs().fillna(0.0)
    return float((w * diffs).sum())


@dataclass
class BrierDecomposition:
    reliability: float  # lower is better; calibration loss
    resolution: float  # higher is better; how varied predictions are
    uncertainty: float  # baseline variance of outcomes
    brier: float  # should equal reliability - resolution + uncertainty

    def asdict(self) -> dict:
        return {
            "reliability": self.reliability,
            "resolution": self.resolution,
            "uncertainty": self.uncertainty,
            "brier": self.brier,
        }


def brier_decomposition(
    probs: np.ndarray, outcomes: np.ndarray, bins: np.ndarray = DEFAULT_BINS
) -> BrierDecomposition:
    """Murphy (1973) decomposition: Brier = reliability - resolution + uncertainty.

    Operates on the pooled 1X2 flattened {(p_ij, y_ij)} pairs.
    """
    p, o = _pool_probs_outcomes(np.asarray(probs), np.asarray(outcomes))
    n_total = len(p)
    o_bar = o.mean()
    uncertainty = o_bar * (1 - o_bar)

    idx = np.clip(np.digitize(p, bins, right=False) - 1, 0, len(bins) - 2)
    rel = 0.0
    res = 0.0
    for b in range(len(bins) - 1):
        mask = idx == b
        nb = int(mask.sum())
        if nb == 0:
            continue
        pb = p[mask].mean()
        ob = o[mask].mean()
        rel += (nb / n_total) * (pb - ob) ** 2
        res += (nb / n_total) * (ob - o_bar) ** 2

    brier = float(((p - o) ** 2).mean())
    return BrierDecomposition(
        reliability=float(rel),
        resolution=float(res),
        uncertainty=float(uncertainty),
        brier=brier,
    )


def plot_reliability_png(
    probs: np.ndarray,
    outcomes: np.ndarray,
    out_path: str | Path,
    title: str = "Reliability diagram",
    bins: np.ndarray = DEFAULT_BINS,
) -> Path:
    """Static matplotlib PNG, for the methodology PDF."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    tbl = reliability_table(probs, outcomes, bins)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(5.5, 5))
    ax.plot([0, 1], [0, 1], "k--", linewidth=1, label="perfect calibration")
    sub = tbl.dropna(subset=["mean_predicted", "observed_frequency"])
    ax.plot(sub["mean_predicted"], sub["observed_frequency"], "o-", label="observed")
    # Bar plot of bin counts on secondary axis
    ax2 = ax.twinx()
    ax2.bar(tbl["bin_mid"], tbl["n"], width=0.08, alpha=0.18, color="gray")
    ax2.set_ylabel("# forecasts per bin", color="gray")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xlabel("Predicted probability")
    ax.set_ylabel("Observed frequency")
    ece = expected_calibration_error(probs, outcomes, bins)
    ax.set_title(f"{title}\nECE = {ece:.3f}")
    ax.legend(loc="upper left", fontsize=8)
    fig.tight_layout()
    fig.savefig(out_path, dpi=130)
    plt.close(fig)
    return out_path


def plot_reliability_plotly(
    probs: np.ndarray, outcomes: np.ndarray, title: str = "Reliability diagram",
    bins: np.ndarray = DEFAULT_BINS,
):
    """Return a plotly.graph_objects.Figure."""
    import plotly.graph_objects as go

    tbl = reliability_table(probs, outcomes, bins)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode="lines",
                             line=dict(dash="dash", color="black"),
                             name="perfect calibration"))
    sub = tbl.dropna(subset=["mean_predicted", "observed_frequency"])
    fig.add_trace(go.Scatter(x=sub["mean_predicted"], y=sub["observed_frequency"],
                             mode="markers+lines", name="observed"))
    fig.add_trace(go.Bar(x=tbl["bin_mid"], y=tbl["n"], yaxis="y2",
                         opacity=0.25, name="bin n", marker_color="gray"))
    ece = expected_calibration_error(probs, outcomes, bins)
    fig.update_layout(
        title=f"{title} | ECE={ece:.3f}",
        xaxis=dict(title="Predicted probability", range=[0, 1]),
        yaxis=dict(title="Observed frequency", range=[0, 1]),
        yaxis2=dict(title="# forecasts", overlaying="y", side="right"),
        legend=dict(x=0.02, y=0.98),
    )
    return fig
