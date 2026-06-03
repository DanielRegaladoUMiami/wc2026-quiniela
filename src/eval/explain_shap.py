"""Per-fixture SHAP explanations for the LightGBM 1X2 model.

Generates Shapley values for each WC2026 fixture so the website can show "why our model
predicts X" — a credibility lever for editorial / pool players. Outputs a long-format
parquet with one row per (match_num, class, feature) so the front-end can render top-K
contributing features per match.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import polars as pl

from src.models import gbm as gbm_mod

CLASSES = ["home_win", "draw", "away_win"]


def explain(features_wc: pd.DataFrame, gbm_path: str) -> pd.DataFrame:
    model = gbm_mod.load(gbm_path)
    X = features_wc[model.feature_cols].fillna(0).to_numpy()
    # LightGBM's predict gives shap values when pred_contrib=True; shape = (n, K * (F+1))
    booster = model.booster
    raw = booster.predict(X, pred_contrib=True, num_iteration=booster.best_iteration)
    n, total = raw.shape
    n_features = len(model.feature_cols)
    n_classes = total // (n_features + 1)
    raw = raw.reshape(n, n_classes, n_features + 1)
    rows: list[dict] = []
    for i in range(n):
        match_num = int(features_wc.iloc[i]["match_num"])
        home = features_wc.iloc[i].get("home_team")
        away = features_wc.iloc[i].get("away_team")
        for k in range(n_classes):
            for f_idx, fname in enumerate(model.feature_cols):
                rows.append(
                    {
                        "match_num": match_num,
                        "home_team": home,
                        "away_team": away,
                        "class": CLASSES[k] if k < len(CLASSES) else f"c{k}",
                        "feature": fname,
                        "shap_value": float(raw[i, k, f_idx]),
                        "feature_value": float(X[i, f_idx]),
                    }
                )
    return pd.DataFrame(rows)


def top_k_per_match(shap_df: pd.DataFrame, k: int = 5) -> pd.DataFrame:
    """For each (match_num, class), keep the top-K features by |shap_value|."""
    s = shap_df.copy()
    s["abs_shap"] = s["shap_value"].abs()
    s = s.sort_values(["match_num", "class", "abs_shap"], ascending=[True, True, False])
    return s.groupby(["match_num", "class"]).head(k).drop(columns=["abs_shap"])


def main() -> int:
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--features", default="data/processed/features_wc2026.parquet")
    p.add_argument("--gbm-path", default="data/models/lgbm_pre_euro24.txt")
    p.add_argument("--out", default="data/processed/shap_wc2026.parquet")
    p.add_argument("--top-k", type=int, default=5)
    args = p.parse_args()

    wc = pl.read_parquet(args.features).to_pandas()
    wc = wc[wc["home_team"].notna()].reset_index(drop=True)
    print(f"Computing SHAP for {len(wc)} fixtures…")
    full = explain(wc, args.gbm_path)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    full.to_parquet(out, compression="zstd")
    print(f"Wrote {len(full):,} rows → {out}")
    top = top_k_per_match(full, k=args.top_k)
    top_out = out.with_name(out.stem + f"_top{args.top_k}.parquet")
    top.to_parquet(top_out, compression="zstd")
    print(f"Wrote {len(top):,} top-{args.top_k} rows → {top_out}")
    # Preview
    sample = top[top["match_num"] == top["match_num"].iloc[0]]
    print("\nExample (one match):")
    print(sample[["class", "feature", "shap_value", "feature_value"]].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
