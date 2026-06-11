# Operations Runbook

> Daily and post-match procedures during the WC 2026 tournament (June 11 – July 19, 2026). Must be executable by Daniel **or** a backup human with repo access.
>
> **Honesty note:** the refresh is **semi-manual** in v1. There is no `src.live.update_loop`
> or `src.live.ingest_live` — the steps below are the real, working pipeline.

## The pipeline (one full cycle)

```bash
make data-refresh   # Elo + ESPN odds + Kalshi + Wikipedia, rebuild match log
make features       # rebuild the feature store
make sim            # predict_wc2026: fit DC as-of today, blend, anchor to market, 50k sims
make quiniela       # pool entries + bracket picks from the latest sim run → data/picks/
```

`make sim` requires `data/processed/{matches,features_wc2026,elo_ratings_history}.parquet`
(produced by `data-refresh` + `features`) and uses `data/processed/market_odds_wc2026.parquet`
for the market anchor when present. `make quiniela` needs only a sim run on disk, so picks
can always be regenerated from the last good sim even if a fetch fails.

## Daily morning (06:00 ET)

1. `make data-refresh` — requires `ODDS_API_KEY` etc. in `.env`; see `.env.example`.
2. Check the de-vigged market snapshot exists and is fresh:
   `data/processed/market_odds_wc2026.parquet` (the quiniela stamps `market_anchored: false`
   in its JSON if it's missing — that's the tell).
3. Update `data/manual/injuries.csv` and `data/manual/lineups_predicted.csv` from ESPN / Twitter.
4. `make features && make sim && make quiniela`
5. Review `data/picks/<sim_run>/quiniela.md`, commit + push → HF Space rebuilds.

## After every match (final whistle)

1. Append the result to the match log source, rerun `uv run python -m src.data.build_match_log`.
2. `make sim` with a fresh `--asof` (defaults to today via `src.predict_wc2026`).
3. `make quiniela` — regenerates entries + bracket for the remaining slate.
4. Commit + push. Post `Today's picks` thread to Twitter (optional; `src.live.twitter_thread`).

## Failure modes

| Symptom | Action |
|---|---|
| Odds/Kalshi API 5xx | Cache last-known-good; rerun in 30 min; quiniela falls back to model-only with a caveat stamp |
| HF Space build fails | Pin to GH Pages fallback; investigate later |
| Bayesian NUTS divergences > 5% | Inspect `notebooks/04_bayesian_diagnostics.ipynb`, fall back to MAP estimate via `--fast` flag |
| Wikipedia result wrong | Override in `data/manual/results_override.csv`; rerun update |
| Sim run has absurd expected goals | Pre-canonicalization name fallback — the picks layer is immune (it rebuilds joints from the 1X2 via `src.models.dc_joint`), but re-run the sim after fixing names |

## Emergency contacts

- TBD backup human with repo access

## Pre-tournament freeze checklist (June 8–10)

- [ ] Final market + Kalshi snapshot on disk
- [ ] Lock v1 picks for opening matchday: `make quiniela`, commit `data/picks/`
- [ ] Verify all GH Actions cron schedules
- [ ] Confirm HF Space resources sufficient
- [ ] Test end-to-end pipeline with a fake result
