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

# wc2026-quiniela

State-of-the-art ML ensemble to predict every match of the **FIFA World Cup 2026** (kickoff June 11, 2026) and optimize quiniela / pool entries across multiple scoring formats (1X2, exact score, bracket).

> **Live dashboard**: https://huggingface.co/spaces/DanielRegaladoCardoso/wc2026-quiniela
> **Source**: https://github.com/DanielRegaladoUMiami/wc2026-quiniela
> **Live picks site**: TBD (HF Spaces). **Backtest report**: TBD (`METHODOLOGY.md`).

## What this is

An open, reproducible pipeline that combines four predictive models and turns their joint output into pool-EV-optimal picks:

1. **Dixon-Coles bivariate Poisson** — classical football goal model with low-score correlation correction (via [`penaltyblog`](https://github.com/martineastwood/penaltyblog)).
2. **Hierarchical Bayesian Poisson** (PyMC) — partial pooling on team attack/defense ratings, essential for national teams with sparse match history.
3. **LightGBM** — gradient-boosted 1X2 / score / BTTS classifiers on engineered features (Elo, FIFA rank, form, xG, squad value, venue, travel, altitude, rest).
4. **Kalshi prediction-market** — sharp implied probabilities used both as a feature in the stacker **and** as a baseline to beat.

A meta-learner stacks the four, isotonic calibration enforces honest probabilities, and a 50,000-iteration Monte Carlo simulation of the 104-match bracket produces per-team advancement probabilities and per-match score-line distributions. A strategy layer then maximizes expected pool points (not argmax) with a contrarian premium estimated from public-pick proxies.

## Data sources (all free)

| Source | What | Loader |
|---|---|---|
| Kaggle `martj42/international-football-results-from-1872-to-2017` | Complete international match log | `kaggle` CLI |
| [eloratings.net](https://www.eloratings.net/) | Daily-updated World Football Elo | scraper |
| FIFA Rankings | Official monthly rankings | scraper |
| [RSSSF](http://www.rsssf.org/) | Definitive historical archive | scraper |
| [StatsBomb Open Data](https://github.com/statsbomb/open-data) | xG event-level (WC18/22, Euro20/24, Copa24) | `statsbombpy` |
| FBref | Player & team stats | `soccerdata` |
| Transfermarkt | Squad market values | `transfermarkt-api` |
| Wikipedia | Squads, live results | `wikipedia-api` |
| Kalshi | WC 2026 market prices | REST API |
| ESPN Scoreboard API | Live results cross-check | REST |

## Repo layout

```
src/
  data/        # fetchers + unified match log builder
  features/    # Elo, form, SPI ridge, venue, squad, market features
  models/      # Dixon-Coles, PyMC Bayesian, LightGBM, stacker, calibration
  sims/        # Monte Carlo bracket + penalty shootout + WC 2026 fixture topology
  strategy/    # pool EV, public-pick estimator, entry portfolio optimization
  eval/        # RPS / log-loss / walk-forward backtest with anti-leakage assertions
  live/        # live ingest + post-match update orchestrator
web/           # Gradio app (Spaces) + static fallback
configs/       # YAML model + rubric configs
notebooks/     # EDA, model fits, backtest results, strategy sensitivity
tests/
```

## Quick start

```bash
git clone https://github.com/DanielRegaladoUMiami/wc2026-quiniela.git
cd wc2026-quiniela

uv sync --extra dev
source .venv/bin/activate

# build the unified match log (Day 1 scope, requires Kaggle creds)
make data

pytest

# launch local dashboard (later)
gradio web/app.py
```

## Methodology

See [`METHODOLOGY.md`](METHODOLOGY.md) for the mathematical details, anti-leakage protocol, backtest tournaments and metrics (Ranked Probability Score, log loss, ROI vs. Pinnacle closing).

## Operations during the tournament

See [`RUNBOOK.md`](RUNBOOK.md) for the daily ops loop (post-matchday refit, picks push, fallback procedures).

## License

[Apache 2.0](LICENSE). Models are wrong; some are useful. Not financial advice.

## Author

Daniel Regalado — MS Business Analytics, University of Miami.
