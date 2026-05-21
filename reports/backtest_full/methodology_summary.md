# Backtest methodology summary

Generated: 2026-05-21T12:20:01

## Design

- **Walk-forward refit**: Dixon–Coles and Bayesian-MAP are re-fit before every distinct match date in each tournament; the harness asserts `predictor.fit_asof_date == match_date` and the predictors filter their training set to `date < asof_date`.
- **GBM**: uses a pre-trained snapshot whose training cutoff is strictly before the tournament start (e.g. `lgbm_pre_wc22.txt` for WC2022, `lgbm_pre_euro24.txt` for Euro 2024 / Copa 2024). For older tournaments without a leakage-safe snapshot, GBM is skipped.
- **Bayesian fast mode**: backtest uses `pm.find_MAP()` per refit rather than full NUTS (refitting NUTS hundreds of times across tournaments is infeasible). The final WC2026 forecast uses full HMC.
- **Bootstrap**: 1000 resamples for RPS 95% CI.

## Results table

| tournament   | model    |   n |    rps | rps_95ci         |   log_loss |   brier |   accuracy |    ece |
|:-------------|:---------|----:|-------:|:-----------------|-----------:|--------:|-----------:|-------:|
| afcon19      | bayesian |  52 | 0.2009 | [0.1698, 0.2381] |     1.019  |  0.205  |     0.5    | 0.0596 |
| afcon19      | dc       |  52 | 0.1894 | [0.1549, 0.2262] |     0.9712 |  0.1931 |     0.5577 | 0.0635 |
| afcon21      | bayesian |  52 | 0.2032 | [0.1538, 0.2525] |     1.0537 |  0.2097 |     0.5    | 0.0766 |
| afcon21      | dc       |  52 | 0.2021 | [0.1625, 0.2430] |     1.028  |  0.2093 |     0.4615 | 0.0946 |
| afcon23      | bayesian |  52 | 0.2181 | [0.1739, 0.2680] |     1.1232 |  0.2268 |     0.4231 | 0.09   |
| afcon23      | dc       |  52 | 0.2125 | [0.1732, 0.2558] |     1.1023 |  0.2236 |     0.3846 | 0.0877 |
| afcon23      | gbm      |  52 | 0.2168 | [0.1753, 0.2658] |     1.1124 |  0.2253 |     0.4231 | 0.0788 |
| asian19      | bayesian |  51 | 0.1889 | [0.1532, 0.2268] |     0.8944 |  0.1745 |     0.6275 | 0.0575 |
| asian19      | dc       |  51 | 0.1733 | [0.1347, 0.2214] |     0.8224 |  0.1576 |     0.7255 | 0.0613 |
| asian23      | bayesian |  51 | 0.193  | [0.1502, 0.2396] |     0.972  |  0.1943 |     0.4902 | 0.0548 |
| asian23      | dc       |  51 | 0.172  | [0.1283, 0.2171] |     0.9064 |  0.1796 |     0.5686 | 0.0425 |
| asian23      | gbm      |  51 | 0.1571 | [0.1188, 0.1977] |     0.8377 |  0.1652 |     0.5686 | 0.0676 |
| copa19       | bayesian |  26 | 0.1743 | [0.1386, 0.2135] |     0.97   |  0.2017 |     0.5385 | 0.0875 |
| copa19       | dc       |  26 | 0.179  | [0.1371, 0.2211] |     0.9904 |  0.2044 |     0.5    | 0.0927 |
| copa21       | bayesian |  28 | 0.158  | [0.1094, 0.2165] |     0.9147 |  0.1765 |     0.6071 | 0.0853 |
| copa21       | dc       |  28 | 0.1671 | [0.1218, 0.2202] |     0.9287 |  0.1838 |     0.5357 | 0.1062 |
| copa24       | bayesian |  32 | 0.1765 | [0.1142, 0.2407] |     0.9453 |  0.184  |     0.5625 | 0.11   |
| copa24       | dc       |  32 | 0.1545 | [0.1098, 0.2045] |     0.8686 |  0.1689 |     0.5625 | 0.1116 |
| copa24       | gbm      |  32 | 0.146  | [0.1163, 0.1794] |     0.8428 |  0.1641 |     0.625  | 0.0921 |
| euro16       | bayesian |  51 | 0.2365 | [0.1963, 0.2778] |     1.1322 |  0.2253 |     0.4118 | 0.1135 |
| euro16       | dc       |  51 | 0.2453 | [0.2053, 0.2872] |     1.1431 |  0.2318 |     0.3529 | 0.1321 |
| euro20       | bayesian |  51 | 0.1851 | [0.1460, 0.2305] |     0.9445 |  0.1878 |     0.5686 | 0.0713 |
| euro20       | dc       |  51 | 0.1906 | [0.1493, 0.2388] |     0.9504 |  0.1865 |     0.549  | 0.0638 |
| euro24       | bayesian |  51 | 0.2053 | [0.1559, 0.2593] |     1.0594 |  0.2102 |     0.5098 | 0.1285 |
| euro24       | dc       |  51 | 0.2    | [0.1652, 0.2397] |     1.0316 |  0.2074 |     0.4706 | 0.0557 |
| euro24       | gbm      |  51 | 0.188  | [0.1519, 0.2263] |     1.0008 |  0.1994 |     0.5098 | 0.0732 |
| wc14         | bayesian |  64 | 0.2295 | [0.1910, 0.2716] |     1.0559 |  0.2098 |     0.5312 | 0.0599 |
| wc14         | dc       |  64 | 0.1902 | [0.1571, 0.2269] |     0.9195 |  0.1803 |     0.625  | 0.079  |
| wc18         | bayesian |  64 | 0.2348 | [0.2040, 0.2664] |     1.0853 |  0.2189 |     0.4219 | 0.0594 |
| wc18         | dc       |  64 | 0.2088 | [0.1748, 0.2470] |     0.9775 |  0.1945 |     0.625  | 0.1121 |
| wc22         | bayesian |  64 | 0.2344 | [0.2000, 0.2733] |     1.1137 |  0.222  |     0.4219 | 0.0818 |
| wc22         | dc       |  64 | 0.2218 | [0.1790, 0.2687] |     1.0582 |  0.2067 |     0.4844 | 0.0805 |
| wc22         | gbm      |  64 | 0.2256 | [0.1864, 0.2699] |     1.0827 |  0.2101 |     0.5156 | 0.0671 |

## Brier decomposition (Murphy 1973)

| tournament   | model    |   reliability |   resolution |   uncertainty |   brier |   n |
|:-------------|:---------|--------------:|-------------:|--------------:|--------:|----:|
| afcon19      | bayesian |        0.0073 |       0.0219 |        0.2222 |  0.205  |  52 |
| afcon19      | dc       |        0.007  |       0.0351 |        0.2222 |  0.1931 |  52 |
| afcon21      | bayesian |        0.0156 |       0.0306 |        0.2222 |  0.2097 |  52 |
| afcon21      | dc       |        0.0159 |       0.0298 |        0.2222 |  0.2093 |  52 |
| afcon23      | bayesian |        0.0173 |       0.0124 |        0.2222 |  0.2268 |  52 |
| afcon23      | dc       |        0.0185 |       0.017  |        0.2222 |  0.2236 |  52 |
| afcon23      | gbm      |        0.0136 |       0.0129 |        0.2222 |  0.2253 |  52 |
| asian19      | bayesian |        0.0089 |       0.0552 |        0.2222 |  0.1745 |  51 |
| asian19      | dc       |        0.008  |       0.0741 |        0.2222 |  0.1576 |  51 |
| asian23      | bayesian |        0.0058 |       0.035  |        0.2222 |  0.1943 |  51 |
| asian23      | dc       |        0.0049 |       0.0516 |        0.2222 |  0.1796 |  51 |
| asian23      | gbm      |        0.012  |       0.0646 |        0.2222 |  0.1652 |  51 |
| copa19       | bayesian |        0.0207 |       0.0399 |        0.2222 |  0.2017 |  26 |
| copa19       | dc       |        0.03   |       0.0478 |        0.2222 |  0.2044 |  26 |
| copa21       | bayesian |        0.0176 |       0.0646 |        0.2222 |  0.1765 |  28 |
| copa21       | dc       |        0.0193 |       0.0565 |        0.2222 |  0.1838 |  28 |
| copa24       | bayesian |        0.022  |       0.0571 |        0.2222 |  0.184  |  32 |
| copa24       | dc       |        0.0231 |       0.0744 |        0.2222 |  0.1689 |  32 |
| copa24       | gbm      |        0.012  |       0.0716 |        0.2222 |  0.1641 |  32 |
| euro16       | bayesian |        0.0166 |       0.0106 |        0.2222 |  0.2253 |  51 |
| euro16       | dc       |        0.0197 |       0.0106 |        0.2222 |  0.2318 |  51 |
| euro20       | bayesian |        0.0089 |       0.0413 |        0.2222 |  0.1878 |  51 |
| euro20       | dc       |        0.0101 |       0.0476 |        0.2222 |  0.1865 |  51 |
| euro24       | bayesian |        0.0257 |       0.0366 |        0.2222 |  0.2102 |  51 |
| euro24       | dc       |        0.0039 |       0.0213 |        0.2222 |  0.2074 |  51 |
| euro24       | gbm      |        0.0084 |       0.0319 |        0.2222 |  0.1994 |  51 |
| wc14         | bayesian |        0.0062 |       0.0191 |        0.2222 |  0.2098 |  64 |
| wc14         | dc       |        0.01   |       0.0498 |        0.2222 |  0.1803 |  64 |
| wc18         | bayesian |        0.0076 |       0.0127 |        0.2222 |  0.2189 |  64 |
| wc18         | dc       |        0.0256 |       0.0515 |        0.2222 |  0.1945 |  64 |
| wc22         | bayesian |        0.0088 |       0.0089 |        0.2222 |  0.222  |  64 |
| wc22         | dc       |        0.0106 |       0.0261 |        0.2222 |  0.2067 |  64 |
| wc22         | gbm      |        0.0137 |       0.024  |        0.2222 |  0.2101 |  64 |

## Runtime: 2216.2s total across 33 runs

## Failures / skipped

| tournament   | model   | error                                                                                           |
|:-------------|:--------|:------------------------------------------------------------------------------------------------|
| wc14         | gbm     | No suitable pre-tournament GBM snapshot for wc14 (would leak — tournament start=2014-06-12).    |
| wc18         | gbm     | No suitable pre-tournament GBM snapshot for wc18 (would leak — tournament start=2018-06-14).    |
| euro16       | gbm     | No suitable pre-tournament GBM snapshot for euro16 (would leak — tournament start=2016-06-10).  |
| euro20       | gbm     | No suitable pre-tournament GBM snapshot for euro20 (would leak — tournament start=2021-06-11).  |
| copa19       | gbm     | No suitable pre-tournament GBM snapshot for copa19 (would leak — tournament start=2019-06-14).  |
| copa21       | gbm     | No suitable pre-tournament GBM snapshot for copa21 (would leak — tournament start=2021-06-13).  |
| afcon19      | gbm     | No suitable pre-tournament GBM snapshot for afcon19 (would leak — tournament start=2019-06-21). |
| afcon21      | gbm     | No suitable pre-tournament GBM snapshot for afcon21 (would leak — tournament start=2022-01-09). |
| asian19      | gbm     | No suitable pre-tournament GBM snapshot for asian19 (would leak — tournament start=2019-01-05). |
