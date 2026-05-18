# Operations Runbook

> Daily and post-match procedures during the WC 2026 tournament (June 11 – July 19, 2026). Must be executable by Daniel **or** a backup human with repo access.

## Daily morning (06:00 ET)

1. Pull latest data: `make data-refresh`
2. Check Kalshi markets ingested OK: tail `data/raw/kalshi/markets_timeseries.parquet`
3. Update `data/manual/injuries.csv` and `data/manual/lineups_predicted.csv` from ESPN / Twitter
4. Trigger live update: `make live-update`
5. Verify site rebuilt: open https://huggingface.co/spaces/DanielRegaladoUMiami/wc2026-quiniela (TBD URL)
6. Verify GH Pages fallback updated: TBD URL

## After every match (final whistle)

1. Append result to `data/raw/matches/wc2026_results.parquet` via `python -m src.live.ingest_live --match-id <id>` (auto-cross-checks ESPN + Wikipedia)
2. `python -m src.live.update_loop`
   - Re-fits Bayesian posterior (~3 min)
   - Re-simulates remaining bracket (~5 min)
   - Regenerates picks for all rubrics
   - Commits + pushes → HF Space auto-rebuilds
3. Post `Today's picks` thread to Twitter (optional; GH Action handles it)

## Failure modes

| Symptom | Action |
|---|---|
| Kalshi API 5xx | Cache last-known-good; rerun in 30 min |
| HF Space build fails | Pin to GH Pages fallback; investigate later |
| Bayesian NUTS divergences > 5% | Inspect `notebooks/04_bayesian_diagnostics.ipynb`, fall back to MAP estimate via `--fast` flag |
| Wikipedia result wrong | Override in `data/manual/results_override.csv`; rerun update |

## Emergency contacts

- TBD backup human with repo access

## Pre-tournament freeze checklist (June 8–10)

- [ ] Final Kalshi market snapshot
- [ ] Lock v1 picks for opening matchday
- [ ] Verify all GH Actions cron schedules
- [ ] Confirm HF Space resources sufficient
- [ ] Test end-to-end pipeline with a fake result
