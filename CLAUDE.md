# CLAUDE.md — wc2026-quiniela

Guidance for Claude Code when working in this repo. Read before editing.

## What this project is

A **market-aware, leakage-free** ML ensemble that predicts every match of the 2026 FIFA
World Cup (48 teams, 104 matches, kickoff **2026-06-11**) and turns the joint output into
pool-EV-optimal quiniela / bracket picks.

**Honesty bar (non-negotiable).** This is a public portfolio + job-search piece. Every
published number must be reproducible from data in the repo. Do **not** ship claims we
cannot back. The honest, reproduced headline is **pooled walk-forward RPS ≈ 0.197 (DC) /
0.208 (Bayes) / 0.192 (GBM)** over 689 matches — *market-level, no leakage*. The goal for
v1 is "market-aware and honestly-validated with CLV reported", not an unbacked
"beats-the-house" claim. We *earn* the strong claim with the CLV number, we don't assert it.

## Stack & conventions

- **Python 3.11–3.12**, deps via **`uv`** (never `pip`). `uv.lock` **is committed** — keep it
  in sync (`uv lock` after changing `pyproject.toml`) so CI and the HF Space don't drift.
- **ruff** for lint+format (config in `pyproject.toml`: line-length 100, rules `E,F,I,B,UP,N,SIM,RUF`,
  `E501` ignored). Run `uv run ruff check src tests` and `uv run ruff format src tests web`
  before committing. A `.pre-commit-config.yaml` enforces this.
- **Commits:** Daniel is the sole author. **Never** add a `Co-Authored-By` trailer.
- **Document in the repo, not chat:** decisions live in `README.md`, `METHODOLOGY.md`,
  `RUNBOOK.md`, and `ROADMAP.md` — update them in lockstep with code.
- **Secrets:** API keys go in `.env` (gitignored), never committed, never pasted in chat.
  `.env.example` lists the required names. Current: `ODDS_API_KEY` (the-odds-api.com),
  `KAGGLE_USERNAME`/`KAGGLE_KEY`, `KALSHI_*` if used.

## Architecture (the four-model ensemble)

```
src/
  data/      fetchers (fetch_*.py) + unified log (build_match_log.py), player/team tables
  features/  Elo (elo.py), form (form.py), feature store (build_table.py)
  models/    dixon_coles.py · bayesian.py (PyMC) · gbm.py (LightGBM) · stacker.py (+ train_stacker.py)
  sims/      tournament.py (Monte Carlo bracket) · bracket_2026.py (WC2026 topology) · penalties.py
  strategy/  pool_ev.py · public_estimator.py · bracket_picks.py · optimize_entries.py
  eval/      rps.py · calibration.py · walk_forward.py · backtest_runner.py · compare_models.py
  live/      twitter_thread.py  (NOTE: update_loop.py / ingest_live.py are referenced but DO NOT exist yet)
web/         Gradio app (web/app.py) — HF Space
site/        Next.js static site — GitHub Pages  (⚠️ see site/AGENTS.md: this is NOT the Next.js you know)
configs/     data_sources.yaml + rubric YAMLs
data/        raw/ processed/ sims/ models/ (most parquets gitignored; manual/, fixtures/, latest sim_run tracked)
```

The stacker meta-learns over the four base models out-of-fold; isotonic/sigmoid calibration
enforces honest probabilities; a Monte Carlo sim of the 104-match bracket yields advancement
+ score-line distributions; the strategy layer maximizes expected pool points (not argmax).

## Known issues being fixed (June 2026 sprint — see ROADMAP.md / task list)

These are real and verified — do not assume the repo is clean:
- **Data is stale**: last played match is 2026-03-31; the June pre-WC window must be re-pulled.
- **No sharp market on disk**: Kalshi snapshot is the wrong (novelty) market; Pinnacle empty.
  The market anchor + devig + **CLV** are the highest-EV work. Odds via the-odds-api.com.
- **Served stacker uses `IdentityCalibrator`** (real calibrators are computed then discarded).
- **Bayesian joint is independent-Poisson** (only Dixon-Coles is correlated) → misprices
  draws / correct-score / BTTS / totals. Apply DC `tau` before the sim.
- **Makefile targets drift from real module names** (`fetch_kalshi`→`fetch_kalshi_markets`,
  `fetch_wikipedia_squads`→`fetch_wiki_squads`; `fetch_rsssf`/`fetch_fifa_ranking`/
  `src.live.update_loop` don't exist). Use real module names; fix the Makefile when touched.
- **sim→optimizer schema mismatch** breaks the bracket optimizer (only champion slot fills).
- Availability (`data/manual/injuries.csv`, `lineups_predicted.csv`) are empty stubs.

## Commands

```bash
uv sync --extra dev                          # install (lockfile-frozen in CI)
uv run ruff check src tests && uv run ruff format --check src tests   # lint (CI gate)
uv run pytest -ra                            # tests
uv run python -m src.data.build_match_log    # rebuild unified match log
uv run python -m src.sims.tournament --n 50000 --fixtures wc2026      # Monte Carlo bracket
uv run gradio web/app.py                     # local dashboard
```

Prefer `uv run python -m <module>` over bare `python` so the locked env is used.
Never claim CI is green without actually running the lint + tests above.
