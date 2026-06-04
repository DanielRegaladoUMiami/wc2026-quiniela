"""Compute the model's edge over the market for the WC2026 group stage.

"Edge" = our (pure-model) probability minus the de-vigged market probability for each
1X2 outcome. A positive edge on an outcome means the model thinks it is more likely than
the closing line implies — i.e. potential betting / pool value. This is the data behind
the "where we beat the house" board.

Output: data/processed/edge_wc2026.parquet
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import polars as pl

from src.predict_wc2026 import build_predictor

OUT = Path("data/processed/edge_wc2026.parquet")
LABELS = ("home", "draw", "away")


def score_matrix_to_1x2(sm: np.ndarray) -> np.ndarray:
    """Marginal P(home win), P(draw), P(away win) from a score-matrix."""
    p_home = np.tril(sm, -1).sum()
    p_draw = np.trace(sm)
    p_away = np.triu(sm, 1).sum()
    v = np.array([p_home, p_draw, p_away], dtype=float)
    return v / v.sum()


def build(asof: date) -> pd.DataFrame:
    # Pure model (market_weight=0) so the comparison to the market is honest.
    predict, _ = build_predictor(
        asof,
        gbm_path="data/models/lgbm_pre_euro24.txt",
        bayesian_path="data/models/bayesian_wc2026.nc",
        stacker_path="data/models/stacker.pkl",
        market_weight=0.0,
    )
    market = pl.read_parquet("data/processed/market_odds_wc2026.parquet").to_pandas()

    rows = []
    for _, m in market.iterrows():
        home, away = m["home_team"], m["away_team"]
        sm = predict(home, away)
        model = score_matrix_to_1x2(sm)
        mkt = np.array([m["p_home_market"], m["p_draw_market"], m["p_away_market"]])
        edge = model - mkt
        best = int(np.argmax(edge))
        rows.append(
            {
                "date": m["date"],
                "home_team": home,
                "away_team": away,
                "p_home_model": model[0],
                "p_draw_model": model[1],
                "p_away_model": model[2],
                "p_home_market": mkt[0],
                "p_draw_market": mkt[1],
                "p_away_market": mkt[2],
                "edge_home": edge[0],
                "edge_draw": edge[1],
                "edge_away": edge[2],
                "best_edge_side": LABELS[best],
                "best_edge_pts": float(edge[best] * 100),
            }
        )
    df = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT, index=False)
    return df


def main() -> int:
    df = build(date(2026, 6, 10))
    df = df.sort_values("best_edge_pts", ascending=False)
    print(f"wrote {len(df)} matches → {OUT}\n")
    print("TOP 12 EDGES (model vs DraftKings closing line):")
    print(f"{'Match':<30} {'side':>5} {'model':>6} {'mkt':>6} {'edge':>7}")
    print("-" * 58)
    for _, r in df.head(12).iterrows():
        side = r["best_edge_side"]
        pm = r[f"p_{side}_model"] * 100
        pk = r[f"p_{side}_market"] * 100
        match = f"{r['home_team']} v {r['away_team']}"[:29]
        print(f"{match:<30} {side:>5} {pm:>5.0f}% {pk:>5.0f}% {r['best_edge_pts']:>+6.1f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
