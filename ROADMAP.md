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
- [x] Apply the real sigmoid calibrators at serve time — `train_stacker` now ships the
      train-fold meta + val-fold Platt calibrators instead of `IdentityCalibrator`
      (**retrain pending**: needs `data/processed/oof_predictions.parquet` regenerated;
      the committed `stacker.pkl` predates the fix). `min_team_matches` pin still open.
- [ ] Add the de-vigged market as a 4th stacker input + shade toward the close; regenerate OOF with more tournaments.
- [ ] Add **CLV** + market baseline + per-class calibration to the backtest.
- [x] Dixon-Coles `tau` joint at the picks layer (`src.models.dc_joint`: tau-adjusted joints
      reconstructed from the blended 1X2, rho = −0.0565 from the latest full DC fit) —
      tau *inside* the sim, penalty rescale, and the FIFA third-placed lookup remain open.

### Phase 3 — Ship one honest, polished Space (Days 6–9)
- [x] Fix the sim→optimizer schema contract + integration test (`normalize_advancement` in
      `bracket_picks`; end-to-end test on the tracked sim run fills all 6 rounds).
- [x] **The quiniela deliverable**: `make quiniela` (`src.strategy.make_quiniela`) →
      `data/picks/<sim_run>/{quiniela.json, entries.csv, quiniela.md}` — 3 pool entries
      (chalk / moderate / high-variance) + ESPN bracket (chalk + contrarian), with honest
      freshness/market caveats stamped into the artifact.
- [ ] Consolidate to one front-end; add the **Edge** surface (model fair prob vs de-vigged market) + freshness stamp.
- [ ] Correlated score heatmap + real knockout bracket tree + empty states.
- [x] Honestly document refresh as semi-manual (RUNBOOK rewritten to the real pipeline;
      Makefile module names fixed). Live-update cron remains v2.

## Deferred to v2
xG-from-scratch ingestion, real public-ownership data, a fully automated live-ingest pipeline,
CLV-learned blend weights (v1 uses a market-heavy fixed/anchored blend).

## Honesty ledger
Numbers we publish must be reproducible from repo data. Pooled walk-forward RPS reproduced at
0.197 / 0.208 / 0.192 (DC / Bayes / GBM) over 689 matches. The cherry-picked "0.146" was a
single 32-match chalk tournament — not the headline.
