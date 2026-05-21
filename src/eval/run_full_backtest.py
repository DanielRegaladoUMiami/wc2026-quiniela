"""Full multi-tournament, multi-model walk-forward backtest CLI.

Example:
    uv run python -m src.eval.run_full_backtest \\
        --tournaments wc14 wc18 wc22 euro20 euro24 copa19 copa21 copa24 \\
                       afcon19 afcon21 afcon23 \\
        --models dc gbm bayesian --bootstrap 1000 --out reports/backtest_full
"""

from __future__ import annotations

import argparse
import json
import pickle
import time
from datetime import date, datetime
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import polars as pl

from src.eval.calibration import (
    brier_decomposition,
    expected_calibration_error,
    plot_reliability_png,
)
from src.eval.compare_models import (
    build_reliability_decomposition,
    build_results_table,
    to_markdown,
)
from src.eval.tournaments import TOURNAMENTS, resolve_keys
from src.eval.walk_forward import (
    BayesianPredictor,
    DixonColesPredictor,
    GBMPredictor,
    walk_forward,
)

MATCHES_PATH = Path("data/processed/matches.parquet")
FEATURES_PATH = Path("data/processed/features_match_level.parquet")
CACHE_DIR = Path("data/models/cache")

# GBM uses a single model trained with strict <-tournament-start cutoff.
# We use the existing pre-trained snapshots where available, otherwise we
# fall back to the most recent suitable snapshot. Map by tournament.
GBM_MODEL_MAP: dict[str, str] = {
    "wc22": "data/models/lgbm_pre_wc22.txt",
    "euro24": "data/models/lgbm_pre_euro24.txt",
    # For tournaments without a dedicated snapshot, the runner will pick the
    # most-recent snapshot whose training data ends strictly before the
    # tournament start.
}


def _load_matches() -> pd.DataFrame:
    return pl.read_parquet(MATCHES_PATH).to_pandas()


def _load_features() -> pd.DataFrame:
    return pl.read_parquet(FEATURES_PATH).to_pandas()


def _gbm_path_for(t_key: str) -> Optional[str]:
    """Pick a GBM snapshot whose training cutoff is strictly before the tournament start.

    We use lgbm_pre_wc22.txt (train_end ~ 2022-11-20) for everything ≤ Nov 2022,
    and lgbm_pre_euro24.txt (train_end ~ 2024-06-14) for everything after.
    For very old tournaments (pre-2022), only wc22 snapshot was trained on data
    that includes those tournaments → would leak. Skip GBM for those.
    """
    if t_key in GBM_MODEL_MAP:
        return GBM_MODEL_MAP[t_key]
    start = TOURNAMENTS[t_key]["start"]
    # lgbm_pre_wc22 was trained on data with cutoff = 2022-11-20.
    # lgbm_pre_euro24 was trained on data with cutoff = 2024-06-14.
    if start >= date(2024, 6, 14):
        return "data/models/lgbm_pre_euro24.txt"
    if start >= date(2022, 11, 20):
        return "data/models/lgbm_pre_wc22.txt"
    # Older tournaments would leak — skip.
    return None


def _cache_load(model: str, t_key: str):
    p = CACHE_DIR / f"{model}_{t_key}.pkl"
    if not p.exists():
        return None
    try:
        with open(p, "rb") as f:
            return pickle.load(f)
    except Exception:
        return None


def _cache_save(model: str, t_key: str, obj) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    p = CACHE_DIR / f"{model}_{t_key}.pkl"
    try:
        with open(p, "wb") as f:
            pickle.dump(obj, f)
    except Exception as exc:
        print(f"  [cache] failed to save {p}: {exc}")


def run_one(
    matches: pd.DataFrame,
    features: pd.DataFrame,
    t_key: str,
    model_name: str,
    use_cache: bool = True,
) -> tuple[pd.DataFrame, list[dict], dict]:
    """Returns (predictions_df, skipped, meta)."""
    t = TOURNAMENTS[t_key]
    t0 = time.time()

    if use_cache:
        cached = _cache_load(model_name, t_key)
        if cached is not None:
            preds, skipped = cached["predictions"], cached["skipped"]
            meta = {**cached.get("meta", {}), "cache_hit": True}
            return preds, skipped, meta

    if model_name == "dc":
        predictor = DixonColesPredictor(matches)
    elif model_name == "gbm":
        gbm_path = _gbm_path_for(t_key)
        if gbm_path is None:
            raise RuntimeError(
                f"No suitable pre-tournament GBM snapshot for {t_key} "
                f"(would leak — tournament start={t['start']})."
            )
        predictor = GBMPredictor(features, gbm_path, tournament_start=t["start"])
    elif model_name == "bayesian":
        predictor = BayesianPredictor(matches, lookback_years=4)
    else:
        raise ValueError(f"Unknown model {model_name}")

    res = walk_forward(matches, t_key, predictor, model_name=model_name)
    dt = time.time() - t0
    meta = {"runtime_sec": dt, "cache_hit": False, "n_skipped": len(res.skipped)}
    if use_cache:
        _cache_save(
            model_name,
            t_key,
            {"predictions": res.predictions, "skipped": res.skipped, "meta": meta},
        )
    return res.predictions, res.skipped, meta


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tournaments", nargs="+", required=True)
    ap.add_argument("--models", nargs="+", default=["dc", "gbm"], choices=["dc", "gbm", "bayesian"])
    ap.add_argument("--bootstrap", type=int, default=1000)
    ap.add_argument("--out", default="reports/backtest_full")
    ap.add_argument("--no-cache", action="store_true")
    args = ap.parse_args()

    keys = resolve_keys(args.tournaments)
    out_dir = Path(args.out)
    (out_dir / "calibration_plots").mkdir(parents=True, exist_ok=True)

    print("Loading match log & features…")
    matches = _load_matches()
    features = _load_features()

    all_preds: list[pd.DataFrame] = []
    all_skipped: list[dict] = []
    runtimes: list[dict] = []
    failures: list[dict] = []

    for t_key in keys:
        for model in args.models:
            tag = f"{t_key}/{model}"
            print(f"\n=== {tag} ===")
            try:
                preds, skipped, meta = run_one(
                    matches, features, t_key, model, use_cache=not args.no_cache
                )
            except Exception as exc:
                print(f"  FAILED: {exc}")
                failures.append({"tournament": t_key, "model": model, "error": str(exc)})
                continue
            if preds.empty:
                print(f"  WARN: no predictions produced")
                failures.append({"tournament": t_key, "model": model, "error": "no predictions"})
                continue
            all_preds.append(preds)
            for s in skipped:
                all_skipped.append({"tournament": t_key, "model": model, **s})
            runtimes.append({"tournament": t_key, "model": model, **meta})
            # Calibration plot per (tournament, model).
            probs = preds[["p_home", "p_draw", "p_away"]].to_numpy()
            outs = preds["outcome"].astype(int).to_numpy()
            plot_path = out_dir / "calibration_plots" / f"{t_key}_{model}.png"
            plot_reliability_png(
                probs, outs, plot_path, title=f"{t_key} – {model}"
            )
            ece = expected_calibration_error(probs, outs)
            print(f"  n={len(preds)}  ECE={ece:.3f}  runtime={meta['runtime_sec']:.1f}s")

    if not all_preds:
        print("\nNo successful runs.")
        return 1

    full_log = pd.concat(all_preds, ignore_index=True)
    full_log.to_parquet(out_dir / "predictions.parquet", index=False)

    print("\nBuilding results table…")
    results = build_results_table(full_log, n_bootstrap=args.bootstrap)
    results.to_csv(out_dir / "results.csv", index=False)

    reldec = build_reliability_decomposition(full_log)
    reldec.to_csv(out_dir / "reliability_decomposition.csv", index=False)

    if all_skipped:
        pd.DataFrame(all_skipped).to_csv(out_dir / "skipped.csv", index=False)
    if failures:
        pd.DataFrame(failures).to_csv(out_dir / "failures.csv", index=False)
    pd.DataFrame(runtimes).to_csv(out_dir / "runtimes.csv", index=False)

    md_path = out_dir / "methodology_summary.md"
    with open(md_path, "w") as f:
        f.write(_methodology_md(results, reldec, runtimes, failures, args))
    print(f"\nWrote {md_path}")
    print(f"Wrote {out_dir/'results.csv'}")
    print(f"Wrote {out_dir/'reliability_decomposition.csv'}")
    print("\n" + to_markdown(results))
    return 0


def _methodology_md(
    results: pd.DataFrame,
    reldec: pd.DataFrame,
    runtimes: list[dict],
    failures: list[dict],
    args,
) -> str:
    lines = []
    lines.append("# Backtest methodology summary")
    lines.append("")
    lines.append(f"Generated: {datetime.now().isoformat(timespec='seconds')}")
    lines.append("")
    lines.append("## Design")
    lines.append("")
    lines.append("- **Walk-forward refit**: Dixon–Coles and Bayesian-MAP are re-fit "
                 "before every distinct match date in each tournament; the harness "
                 "asserts `predictor.fit_asof_date == match_date` and the predictors "
                 "filter their training set to `date < asof_date`.")
    lines.append("- **GBM**: uses a pre-trained snapshot whose training cutoff is "
                 "strictly before the tournament start (e.g. `lgbm_pre_wc22.txt` for "
                 "WC2022, `lgbm_pre_euro24.txt` for Euro 2024 / Copa 2024). For older "
                 "tournaments without a leakage-safe snapshot, GBM is skipped.")
    lines.append("- **Bayesian fast mode**: backtest uses `pm.find_MAP()` per refit "
                 "rather than full NUTS (refitting NUTS hundreds of times across "
                 "tournaments is infeasible). The final WC2026 forecast uses full HMC.")
    lines.append(f"- **Bootstrap**: {args.bootstrap} resamples for RPS 95% CI.")
    lines.append("")
    lines.append("## Results table")
    lines.append("")
    lines.append(to_markdown(results))
    lines.append("")
    if not reldec.empty:
        lines.append("## Brier decomposition (Murphy 1973)")
        lines.append("")
        lines.append(reldec.round(4).to_markdown(index=False))
        lines.append("")
    if runtimes:
        rt = pd.DataFrame(runtimes)
        total = rt["runtime_sec"].sum()
        lines.append(f"## Runtime: {total:.1f}s total across {len(rt)} runs")
        lines.append("")
    if failures:
        lines.append("## Failures / skipped")
        lines.append("")
        lines.append(pd.DataFrame(failures).to_markdown(index=False))
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
