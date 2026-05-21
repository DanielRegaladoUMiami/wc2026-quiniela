# Methodology — wc2026-quiniela

A reproducible probabilistic model for the FIFA World Cup 2026, designed to produce calibrated 1X2, exact-score, and bracket-advancement probabilities for every one of the 104 matches.

> Author: Daniel Regalado (MS Business Analytics, University of Miami) · Apache 2.0 · [github.com/DanielRegaladoUMiami/wc2026-quiniela](https://github.com/DanielRegaladoUMiami/wc2026-quiniela)

---

## 1. What we predict

For every match `m` we estimate a **joint score-line distribution** over (home goals, away goals):

$$
P_m(H = i, A = j) \quad \text{for } i, j \in \{0, 1, \ldots, 10\}
$$

From this 11×11 matrix we derive every other quantity of interest:

| Question | Derivation |
|---|---|
| P(home wins regulation) | $\sum_{i > j} P_m(i, j)$ |
| P(draw) | $\sum_i P_m(i, i)$ |
| P(over 2.5 goals) | $\sum_{i + j \geq 3} P_m(i, j)$ |
| Expected home goals | $\sum_i i \cdot P(H = i)$ |
| P(team T advances from group) | Monte Carlo over the 3 group matches with tiebreakers |
| P(team T = champion) | Monte Carlo over the full bracket |

The score-matrix abstraction lets a single predictor power every downstream query.

---

## 2. Data

### Training corpus
- **49,286 international matches** since 1872 (Kaggle `martj42/international-football-results-from-1872-to-2017`, updated through 2026-05). Fields: date, home team, away team, goals, tournament, city, country, neutral venue.

### xG ground truth
- **StatsBomb Open Data** — 262 matches with shot-level xG (WC 2018, WC 2022, Euro 2020, Euro 2024, Copa América 2024). The model **does not require xG** since the joint Poisson framework operates on observed goals, but xG is used as a sanity check and for the LightGBM features.

### Derived features
- **Custom Elo ratings** computed by walking the 49k matches chronologically with the World Football Elo conventions: K = {60, 50, 45, 35, 20} for {WC knockout, WC group, continental, qualifier, friendly}; goal-difference multiplier per Davidson (2003); +100 ELO equivalent home advantage; neutral-venue suppression. Output: 98,428 (team, date, rating) records.
- **Rolling form** per team over 5 / 10 / 20 previous matches: points per game, goals for, goals against, goal difference, win rate, plus the same metrics restricted to opponents with Elo ≥ 1900 (tier-aware form).
- **Tournament-importance weight** ∈ {4.0, 3.5, 3.0, 2.5, 2.0, 1.0} mapped from `competition` string.
- **Venue features** for WC 2026 fixtures: altitude, indoor flag, country (USA / Mexico / Canada).
- **Pre-match Elo deltas** and probability of home win implied by Elo (with home advantage adjustment for host-country matches).

### Anti-leakage protocol
- Every feature is computed strictly as of `match_date − 1 day`. Backtest harness asserts this invariant in CI.
- Custom Elo is computed chronologically so the rating before match `m` is independent of `m`'s result.
- StatsBomb event-level data is joined per match only, never used to leak season-level stats.
- For historical tournament backtests (WC18, WC22, Euro24, Copa24), each tournament is held out completely from training and the model is refit at the tournament's pre-kickoff date.

---

## 3. The four base predictors

We deliberately avoid relying on a single model. Each captures a different signal and brings a different inductive bias.

### 3.1 Dixon-Coles bivariate Poisson (1997)

```
log λ_home = μ + att[home] + def[away] + home_advantage
log λ_away = μ + att[away] + def[home]
H ~ Poisson(λ_home),   A ~ Poisson(λ_away)
```

Plus a low-score correction ρ that fixes Poisson's under-prediction of 0-0 and 1-1. Fit via maximum likelihood with exponential time decay ξ = 0.0019 (≈ 1-year half-life). Implementation via [`penaltyblog`](https://github.com/martineastwood/penaltyblog).

### 3.2 Hierarchical Bayesian Poisson (Baio & Blangiardo 2010)

Same likelihood as Dixon-Coles, but with hierarchical priors that partial-pool team strengths toward the global mean:

```
att[team] ~ Normal(0, σ_att);    σ_att ~ HalfNormal(1)
def[team] ~ Normal(0, σ_def);    σ_def ~ HalfNormal(1)
γ_home[team, venue_country] ~ Normal(host_prior, σ_γ)
```

Host-country priors for the 48-team / 3-host WC 2026 are calibrated by hand: μ_USA = 0.25, μ_Mexico = 0.40, μ_Canada = 0.20, μ_other = 0.05 (in goal-rate space). Fit with PyMC 5 + NUTS, 4 chains × 1500 tune + 1500 draws = 6000 posterior samples. Predictions integrate over the posterior, not over a point estimate.

Why we need this: national-team data is sparse. Curaçao has 4 matches in our training window; Cape Verde 5. Without hierarchical pooling, the model assigns ridiculous priors. Partial pooling shrinks small-sample teams toward the global mean and only lets evidence accumulate as we see them play.

### 3.3 LightGBM 1X2 classifier

A gradient-boosted classifier on the engineered feature table:

- `elo_diff`, `home_elo_pre`, `away_elo_pre`, `p_home_win_elo`
- `importance` (tournament weight)
- Rolling form metrics over 5 / 10 / 20 matches × {ppg, gf, ga, gd, win_rate} × {all opponents, top-20 only}
- Days since last match (rest)
- `form_diff_*` (relative form)

LightGBM picks up non-linear interactions that the Poisson models miss (e.g. "elo_diff > 200 but visitor on a 3-game winning streak vs top-20 opponents → flag upset risk"). Tuned with Optuna under TimeSeriesSplit. **Isotonic-calibrated** on a held-out validation window.

### 3.4 Prediction-market features (Kalshi, planned)

Kalshi WC 2026 markets are scraped daily (133 markets currently open) and fed into the stacker as a sharp prior. ESPN-grade systems would also pull Pinnacle closing odds — our current OddsPortal scraper is a placeholder pending a more robust solution (Cloudflare-protected pages).

---

## 4. Stacking and calibration

For each match we collect:
- DC's 1X2 marginal `[p_h_DC, p_d_DC, p_a_DC]`
- LightGBM's 1X2 `[p_h_GBM, p_d_GBM, p_a_GBM]`
- Bayesian's posterior-averaged 1X2 `[p_h_Bay, p_d_Bay, p_a_Bay]`

A **multinomial logistic regression** is trained on out-of-fold predictions across four historical tournaments (WC 2018, WC 2022, Euro 2024, Copa América 2024 — 211 OOF matches total). The learned weights for the home-win class:

| Input | Coefficient |
|---|---|
| `p_dc_h`   | **+1.13** |
| `p_gbm_h`  | +0.65 |
| `p_bay_h`  | +0.03 |
| `p_dc_d`   | −0.76 |
| `p_dc_a`   | −0.37 |
| (others)   | smaller |

Dixon-Coles is the strongest individual home-win signal; LightGBM adds incremental lift; Bayesian's marginal contribution is small once DC is in the model, which is expected because both share the Poisson likelihood. The stacker preserves all three for ensemble diversity even when individual contributions are modest.

Once the 1X2 marginals are blended, we re-weight the Dixon-Coles score matrix so its three sums (lower-triangle, diagonal, upper-triangle) match the blended marginals exactly. This preserves DC's joint shape (which scorelines are likeliest within each outcome) while honoring the consensus on 1X2.

---

## 5. Monte Carlo bracket simulation

Match-level probabilities do not directly answer "what is Argentina's probability of reaching the final?". For that we simulate the entire 104-match bracket many times.

For each simulation:
1. Sample a scoreline for each of the 72 group matches from its joint distribution.
2. Compute group standings, applying FIFA's tiebreakers in order: points → goal difference → goals for → head-to-head goal difference → random.
3. Identify the top-2 from each group and the 8 best third-placed teams.
4. Resolve the 16 Round of 32 fixtures using FIFA's third-placed lookup table.[^1]
5. Sample scorelines for each R32 / R16 / QF / SF / Final match. On knockout ties, simulate a penalty shootout via a logistic on strength differential.
6. Record each team's terminal stage.

[^1]: Current implementation uses a uniform-sampling approximation for the third-placed slot assignment. The official FIFA deterministic table is a known TODO; bias is on the order of one R32 fixture per simulation.

We run **N = 5,000 simulations** (parameter; up to 50k is feasible in under 10 minutes). Aggregating across sims yields per-team probabilities for every stage:

```
P(advance group), P(reach R16), P(reach QF), P(reach SF), P(reach final), P(champion), P(3rd place)
```

---

## 6. Strategy: turning probabilities into pool picks

A calibrated probability is necessary but not sufficient for winning a pool. The trap is to pick the modal outcome. The fix is to compute expected pool points and account for public-pick distributions.

### 6.1 Exact-score pools with partial credit

Rubric: 5 points exact score, 3 points correct goal difference + correct winner, 1 point correct 1X2.

For each candidate pick (i, j) ∈ {0..5}², expected points are:

$$
E[\text{points} \mid (i, j)] = \sum_{i', j'} P_m(i', j') \cdot \text{score}((i, j), (i', j'))
$$

We pick argmax. Frequently the optimal pick is 1-1 or 2-1 even when the modal scoreline is 0-0 — the partial credit favors picks "close to" many real outcomes.

### 6.2 1X2 pools with contrarian dynamics

If Brazil is 50% to win and the public picks Brazil at 80%, picking Brazil yields no edge in pool EV. Instead we maximize:

$$
\text{pool EV}(\text{pick}) = E[\text{points}] \cdot \big(1 - P(\text{public picks same})\big)
$$

The public-pick distribution is estimated as a 50/50 blend of (a) sharp market implied probabilities, when available, and (b) FIFA-rank "square money" priors (favorite always wins).

### 6.3 Bracket pools

We optimize a portfolio of 3-5 entries spanning chalk ↔ moderate contrarian ↔ high variance. Each entry walks the bracket forward, picking each round to maximize round-conditional expected points with optional contrarian penalty on heavily picked outcomes.

---

## 7. Evaluation — what we measure

### 7.1 Ranked Probability Score (RPS)

The primary 1X2 metric, defined for K = 3 ordered outcomes (home win ≺ draw ≺ away win):

$$
\text{RPS} = \frac{1}{K-1} \sum_{k=1}^{K-1} \left( \sum_{j \leq k} p_j - \sum_{j \leq k} o_j \right)^2
$$

Lower is better. Reference points:

| Forecaster | RPS |
|---|---|
| Perfect | 0.000 |
| State-of-the-art academic | ~0.165 |
| Top betting syndicates | 0.165 - 0.175 |
| Sharp bookmaker closing | 0.200 - 0.210 |
| **Our model on Euro 2024** | **0.188** |
| **Our model on WC 2022** | 0.222 (upset-heavy tournament) |
| Uniform forecast [1/3, 1/3, 1/3] | ~0.222 |
| Random | ~0.250 |

WC 2022 was a structural outlier: Argentina-Saudi Arabia, Morocco to the semifinal, Japan beating Germany and Spain. No model performed well on it. Euro 2024 is the cleaner benchmark.

### 7.2 Log loss

Strict-proper scoring rule that heavily penalizes confident wrong predictions. Computed as the mean negative log probability assigned to the actual outcome. We monitor it but optimize for RPS.

### 7.3 Calibration

For probabilistic forecasts, **calibration** is at least as important as **discrimination**. A model that says "70% home win" should be right 70% of the time over many such predictions. We report reliability diagrams (binned predicted-vs-observed) and Expected Calibration Error (ECE) per held-out tournament.

LightGBM is calibrated with isotonic regression on a held-out window. The stacker is currently using identity calibration on top of logistic regression (Platt scaling didn't improve OOF performance with our sample size of 211; isotonic over-fit with the same sample).

### 7.4 ROI vs market

The honest "does this make money?" check: for each historical match where we had model probabilities and sharp-bookmaker odds (Pinnacle closing, vig removed via Shin), we simulate Kelly-fractional bets when the model's edge exceeds the market's, and report cumulative ROI. Pending implementation once odds scraper is robust.

---

## 8. Known limitations and future work

| Limitation | Impact | Plan |
|---|---|---|
| No paid xG data (Opta / StatsBomb Pro) | Models with full xG coverage gain ~0.01-0.02 RPS | Requires licensing |
| OOF training set 211 matches | Stacker calibration over-fits with isotonic | Expand to AFCON, Asian Cup, Nations League |
| FIFA third-placed table approximated | ~1 R32 fixture biased per sim | Parse FIFA regulations PDF |
| Squad changes / injuries | Manual CSV override | Daily Wikipedia scraper |
| In-play model (during match) | Not implemented | Future v3 |
| Pinnacle / sharp odds historical | OddsPortal blocked by Cloudflare | Selenium fallback or paid feed |
| Editorial / human commentary | None | Out of scope for v1 |

---

## 9. Reproducibility

```bash
git clone https://github.com/DanielRegaladoUMiami/wc2026-quiniela.git
cd wc2026-quiniela
uv sync --extra dev
source .venv/bin/activate

make data        # fetch + build canonical match log, Elo, form features
make train       # fit DC, GBM, Bayesian, train stacker
make sim         # 5,000 Monte Carlo simulations
make web         # launch Gradio dashboard
make test        # 48 tests
```

The full pipeline is deterministic given the random seed.

---

## 10. References

- Dixon, M. J., & Coles, S. G. (1997). *Modelling Association Football Scores and Inefficiencies in the Football Betting Market*. Applied Statistics, 46(2), 265-280.
- Baio, G., & Blangiardo, M. (2010). *Bayesian hierarchical model for the prediction of football results*. Journal of Applied Statistics, 37(2), 253-264.
- Constantinou, A. C., & Fenton, N. E. (2012). *Solving the problem of inadequate scoring rules for assessing probabilistic football forecast models*. Journal of Quantitative Analysis in Sports, 8(1).
- Davidson, R. R. (2003). *On the use of margin of victory in Bayesian ranking systems*. Computational Statistics & Data Analysis.
- Shin, H. S. (1993). *Measuring the incidence of insider trading in a market for state-contingent claims*. Economic Journal, 103(420), 1141-1153.

---

*Models are wrong; some are useful. Not financial advice. Apache 2.0 license.*
