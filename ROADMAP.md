# ROADMAP — wc2026-quiniela

Goal: take a genuinely good academic ensemble (leakage-free, market-level RPS) and make it
**market-aware, honestly-validated, and shippable** before kickoff (**2026-06-11**).

The defining gap today is **data + market**, not modeling: data is stale (last played match
2026-03-31), there is no sharp market on disk, and CLV (the gold-standard validation) is
unmeasured. Modeling and backtest discipline are sound. We *earn* the strong claim with the
CLV number; we do not assert it.

## v1 sprint — June 2026 (target ~40h)

### Phase 0 — Honesty & reproducibility (Day 1)
- [x] Commit `uv.lock` (un-ignore) — root cause of ruff 0.7→0.15 CI drift.
- [x] Add root `CLAUDE.md`.
- [ ] CI deterministically green: `ruff check` + `ruff format --check` + `pytest`; add `.pre-commit-config.yaml`.
- [ ] Strip false UI claims (sims count, hardcoded RPS, fake "Live", mislabeled DC heatmap); re-point published `meta.json` to newest sim and regenerate site JSON.
- [ ] Honest README/validation headline (pooled RPS 0.197/0.208/0.192, leakage-free; CLV pending).

### Phase 1 — Real current data (Days 2–4)
- [ ] Re-pull results current-through-today; freshness assertion (fail if max played < today−3); filter unplayed fixtures from training.
- [ ] **Sharp-market fetcher** (the-odds-api.com 1X2 + champion, Kalshi champion) → `data/processed/market_odds_history.parquet`; unit-tested Shin/log-additive de-vig.
- [ ] Populate injuries / predicted XI; trim oversized rosters to the official 26; fix `elo/current.parquet` header parsing.
- [ ] Make the scheduled refresh actually persist; fix Makefile module names.

### Phase 2 — Market-aware, calibrated, CLV-validated (Days 4–6)
- [ ] Apply the real isotonic/sigmoid calibrators at serve time (today: `IdentityCalibrator`); pin one `min_team_matches` across OOF/prod/backtest.
- [ ] Add the de-vigged market as a 4th stacker input + shade toward the close; regenerate OOF with more tournaments.
- [ ] Add **CLV** + market baseline + per-class calibration to the backtest.
- [ ] Fix the joint: Dixon-Coles `tau` before the sim; rescale penalties; load the FIFA third-placed lookup table.

### Phase 3 — Ship one honest, polished Space (Days 6–9)
- [ ] Fix the sim→optimizer schema contract + integration test (today only the champion slot fills).
- [ ] Consolidate to one front-end; add the **Edge** surface (model fair prob vs de-vigged market) + freshness stamp.
- [ ] Correlated score heatmap + real knockout bracket tree + empty states.
- [ ] Live-update cron + consistent `--asof`; end-to-end freeze test, or honestly document refresh as semi-manual.

## Deferred to v2
xG-from-scratch ingestion, real public-ownership data, a fully automated live-ingest pipeline,
CLV-learned blend weights (v1 uses a market-heavy fixed/anchored blend).

## Honesty ledger
Numbers we publish must be reproducible from repo data. Pooled walk-forward RPS reproduced at
0.197 / 0.208 / 0.192 (DC / Bayes / GBM) over 689 matches. The cherry-picked "0.146" was a
single 32-match chalk tournament — not the headline.
