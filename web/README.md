---
title: WC2026 Quiniela
emoji: ⚽
colorFrom: green
colorTo: orange
sdk: gradio
sdk_version: 6.14.0
app_file: web/app.py
pinned: false
license: apache-2.0
---

# WC2026 Quiniela — Gradio dashboard

Interactive UI for the FIFA World Cup 2026 probabilistic prediction system.

## Pages

1. **Home** — next 5 matches, probability bars, recommended picks.
2. **Bracket** — Sankey + treemap from R32 → Champion; sortable 48-team table.
3. **Standings** — 12 group cards with P(advance) bars.
4. **Model vs Market** — backtest cumulative log-loss vs bookmaker line.
5. **Quiniela Picks** — 1X2 / Exact score / Bracket sub-tabs.
6. **Methodology** — pipeline diagram + full `METHODOLOGY.md`.
7. **About** — author / repo / disclaimer.

## Run locally

```bash
uv sync
uv run python web/app.py        # http://127.0.0.1:7860
# or
uv run gradio web/app.py        # hot reload
```

## Deploy to Hugging Face Spaces

1. Create a new Space (Gradio SDK). The YAML block at the top of this README is the
   Spaces configuration — keep it intact.
2. Push the repo:

   ```bash
   git remote add space https://huggingface.co/spaces/<user>/wc2026-quiniela
   git push space main
   ```

3. Spaces will install `requirements.txt` / `pyproject.toml` and launch `web/app.py`
   on port 7860. The cron-refreshed parquet files in `data/sims/sim_run_*/` are
   hot-reloaded via mtime-keyed `lru_cache`.

## Data contract

| File | Purpose |
|------|---------|
| `data/fixtures/wc2026_fixtures.parquet` | 104 matches |
| `data/fixtures/groups.parquet` | 12 × 4 group table |
| `data/sims/sim_run_*/advancement.parquet` | per-team stage probabilities |
| `data/sims/sim_run_*/match_probs.parquet` | per-match 1X2 + xG |
| `data/sims/backtest_gbm_{wc2022,euro2024}.parquet` | backtest predictions |

Missing files degrade gracefully via a "Predictions not generated yet" banner.
