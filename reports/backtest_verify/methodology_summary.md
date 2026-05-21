# Backtest methodology summary

Generated: 2026-05-21T11:50:08

## Design

- **Walk-forward refit**: Dixon–Coles and Bayesian-MAP are re-fit before every distinct match date in each tournament; the harness asserts `predictor.fit_asof_date == match_date` and the predictors filter their training set to `date < asof_date`.
- **GBM**: uses a pre-trained snapshot whose training cutoff is strictly before the tournament start (e.g. `lgbm_pre_wc22.txt` for WC2022, `lgbm_pre_euro24.txt` for Euro 2024 / Copa 2024). For older tournaments without a leakage-safe snapshot, GBM is skipped.
- **Bayesian fast mode**: backtest uses `pm.find_MAP()` per refit rather than full NUTS (refitting NUTS hundreds of times across tournaments is infeasible). The final WC2026 forecast uses full HMC.
- **Bootstrap**: 200 resamples for RPS 95% CI.

## Results table

| tournament   | model   |   n |    rps | rps_95ci         |   log_loss |   brier |   accuracy |    ece |
|:-------------|:--------|----:|-------:|:-----------------|-----------:|--------:|-----------:|-------:|
| copa24       | dc      |  32 | 0.1545 | [0.1098, 0.2042] |     0.8686 |  0.1689 |     0.5625 | 0.1116 |
| copa24       | gbm     |  32 | 0.146  | [0.1185, 0.1791] |     0.8428 |  0.1641 |     0.625  | 0.0921 |
| euro24       | dc      |  51 | 0.2    | [0.1569, 0.2383] |     1.0316 |  0.2074 |     0.4706 | 0.0557 |
| euro24       | gbm     |  51 | 0.188  | [0.1494, 0.2227] |     1.0008 |  0.1994 |     0.5098 | 0.0732 |
| wc22         | dc      |  64 | 0.2218 | [0.1838, 0.2657] |     1.0582 |  0.2067 |     0.4844 | 0.0805 |
| wc22         | gbm     |  64 | 0.2256 | [0.1914, 0.2699] |     1.0827 |  0.2101 |     0.5156 | 0.0671 |

## Brier decomposition (Murphy 1973)

| tournament   | model   |   reliability |   resolution |   uncertainty |   brier |   n |
|:-------------|:--------|--------------:|-------------:|--------------:|--------:|----:|
| copa24       | dc      |        0.0231 |       0.0744 |        0.2222 |  0.1689 |  32 |
| copa24       | gbm     |        0.012  |       0.0716 |        0.2222 |  0.1641 |  32 |
| euro24       | dc      |        0.0039 |       0.0213 |        0.2222 |  0.2074 |  51 |
| euro24       | gbm     |        0.0084 |       0.0319 |        0.2222 |  0.1994 |  51 |
| wc22         | dc      |        0.0106 |       0.0261 |        0.2222 |  0.2067 |  64 |
| wc22         | gbm     |        0.0137 |       0.024  |        0.2222 |  0.2101 |  64 |

## Runtime: 443.1s total across 6 runs
