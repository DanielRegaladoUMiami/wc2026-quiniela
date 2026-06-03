---
title: WC2026 Quiniela
emoji: ⚽
colorFrom: green
colorTo: yellow
sdk: gradio
sdk_version: 6.14.0
app_file: web/app.py
pinned: false
license: apache-2.0
---

# wc2026-quiniela

An ML forecasting system **built to the standards a sharp sportsbook operates on** — de-vigged market anchoring, honest probability calibration, and closing-line-value validation — to price every match of the **FIFA World Cup 2026** (kickoff June 11, 2026) and optimize quiniela / pool entries across multiple scoring formats (1X2, exact score, bracket).

> 🌐 **Static site (Next.js)**: https://danielregaladoumiami.github.io/wc2026-quiniela/
> 🤗 **Interactive dashboard (Gradio + HF Spaces)**: https://huggingface.co/spaces/DanielRegaladoCardoso/wc2026-quiniela
> 📂 **Source**: https://github.com/DanielRegaladoUMiami/wc2026-quiniela
> 📄 **Methodology paper**: [`METHODOLOGY.md`](METHODOLOGY.md)

## Validation (honest, reproduced)

The discipline this project is built on is a **leakage-free walk-forward backtest** (train only
on matches before each test tournament; anti-leakage assertions in `src/eval/walk_forward.py`).
Reproduced pooled **Ranked Probability Score** over 689 historical tournament matches:

| Model | Pooled RPS (1X2) |
|---|---|
| Dixon-Coles | **0.197** |
| Hierarchical Bayesian | 0.208 |
| LightGBM | 0.192 |

That is **market-level** for international-tournament 1X2 — and it holds out-of-sample with no
leakage red flags, which is the part most projects get wrong. The system is built to the same
playbook a sharp book runs: anchor to the de-vigged closing line, calibrate honestly, and grade
yourself on **closing-line value (CLV)** — the real gold standard. CLV measurement is being
finalized for v1 (see [`ROADMAP.md`](ROADMAP.md)); the number is published alongside the model,
earned and shown rather than asserted.

## What this is

An open, reproducible pipeline that combines four predictive models and turns their joint output into pool-EV-optimal picks:

1. **Dixon-Coles bivariate Poisson** — classical football goal model with low-score correlation correction (via [`penaltyblog`](https://github.com/martineastwood/penaltyblog)).
2. **Hierarchical Bayesian Poisson** (PyMC) — partial pooling on team attack/defense ratings, essential for national teams with sparse match history.
3. **LightGBM** — gradient-boosted 1X2 / score / BTTS classifiers on engineered features (Elo, FIFA rank, form, xG, squad value, venue, travel, altitude, rest).
4. **Sharp-market anchor** — de-vigged implied probabilities from the sharp closing line (Pinnacle/Kalshi, via the-odds-api.com), blended into the stacker **and** used as the baseline to beat. *(Market ingestion + de-vig is landing in the June sprint — see [`ROADMAP.md`](ROADMAP.md).)*

A meta-learner stacks the four; isotonic/sigmoid calibration is fit to enforce honest probabilities; and a Monte Carlo simulation of the 104-match bracket produces per-team advancement probabilities and per-match score-line distributions. A strategy layer then maximizes expected pool points (not argmax) with a contrarian premium estimated from public-pick proxies.

> **Status (June 2026):** the historical spine, the four base models and the leakage-free
> backtest are in place. Actively in progress for v1: refreshing data through kickoff, the
> sharp-market anchor + CLV, applying the fitted calibrators at serve time, and one polished
> dashboard. Track it in [`ROADMAP.md`](ROADMAP.md).

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
