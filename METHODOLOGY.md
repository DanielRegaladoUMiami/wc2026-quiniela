# Methodology

> Living document. Updated as models are implemented (Days 6–10 of the build plan).

## Goal

Produce well-calibrated probabilistic predictions for every match of FIFA World Cup 2026, and convert them into pool-EV-optimal quiniela entries.

## Predictive ensemble

### 1. Dixon-Coles bivariate Poisson
Classical model for football scorelines, fixing the well-known under-prediction of low-score draws (0-0, 1-1) by a small correction parameter ρ. Fit with exponential time decay (ξ = 0.0019 ≈ 1-year half-life) using [`penaltyblog`](https://github.com/martineastwood/penaltyblog).

References:
- Dixon & Coles (1997), *Modelling Association Football Scores and Inefficiencies in the Football Betting Market*.

### 2. Hierarchical Bayesian Poisson (PyMC)
```
log λ_home = μ + att[home] + def[away] + γ_home(venue, team)
log λ_away = μ + att[away] + def[home]
att, def ~ Normal(0, σ);  σ ~ HalfNormal(1)
γ_home[team, venue_country] ~ Normal(host_prior, σ_γ)
```
Partial pooling regularizes sparse-data teams toward the overall mean. Host effects for USA / Mexico / Canada are estimated jointly rather than hardcoded — necessary because the 48-team / 3-host format has no historical precedent.

References:
- Baio & Blangiardo (2010), *Bayesian hierarchical model for the prediction of football results*.

### 3. LightGBM
Gradient-boosted classifiers on engineered features. Tuned with Optuna under `TimeSeriesSplit` to prevent look-ahead.

### 4. Kalshi market features
Implied probabilities (de-vigged with Shin's method) enter both as a stacker feature *and* as a benchmark to beat.

### 5. Stacker + calibration
Multinomial logistic regression on out-of-fold base predictions + market features, followed by isotonic calibration per class.

### 6. Monte Carlo bracket
50,000 full-tournament simulations sampling scorelines from the calibrated joint distribution, with a penalty-shootout model for knockout draws.

## Anti-leakage protocol

- All historical features stamped with `feature_date < match_date` (CI-enforced assertion).
- Elo reconstructed from per-match diffs, never current snapshot.
- FBref stats truncated to match date, not season totals.
- Transfermarkt values snapshotted by date.
- Historical-tournament backtests use Pinnacle closing odds (not Kalshi — Kalshi WC markets didn't exist pre-2026).

## Backtest tournaments

WC 2018, WC 2022, Euro 2020, Euro 2024, Copa América 2019/2021/2024, AFCON 2019/2021/2023, Nations League 2020-21 / 2022-23.

## Metrics

- **RPS (Ranked Probability Score)** — primary, target < 0.21 (bookmaker closing ≈ 0.20–0.21).
- Log loss on 1X2.
- Brier on BTTS / Over 2.5.
- Reliability plots.
- ROI vs. Pinnacle closing.

## Known unknowns

- **48-team / 3-host format**: zero historical analog. Bracket priors held wide.
- **Squad sparsity** for minor nations: hierarchical pooling helps; confederation-level priors as fallback.
- **Mid-tournament squad changes**: manual injuries CSV updated daily; star absences trigger -0.5 goal penalty to attack rating (to be calibrated empirically).
