"""Hierarchical Bayesian Poisson goal model (Baio & Blangiardo 2010) with WC2026 host effects.

log λ_home = μ + att[home] + def_[away] + γ[home, venue_country]
log λ_away = μ + att[away] + def_[home]

Team strengths sum-to-zero for identifiability; host-country priors bias γ for USA / Mexico /
Canada to inject WC2026-host knowledge before observing 2026 fixtures.
"""

from __future__ import annotations

import argparse
import warnings
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

import arviz as az
import numpy as np
import pandas as pd
import pymc as pm

HOST_PRIORS: dict[str, float] = {
    "United States": 0.25,
    "USA": 0.25,
    "Mexico": 0.40,
    "Canada": 0.20,
}
DEFAULT_HOST_PRIOR = 0.05


@dataclass
class BayesianModel:
    idata: az.InferenceData
    team_to_idx: dict[str, int]
    venue_to_idx: dict[str, int]
    asof_date: date
    lookback_years: int
    dropped_teams: list[str] = field(default_factory=list)

    @property
    def teams(self) -> list[str]:
        return list(self.team_to_idx.keys())

    def save(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.idata.attrs["team_to_idx"] = ",".join(f"{t}={i}" for t, i in self.team_to_idx.items())
        self.idata.attrs["venue_to_idx"] = ",".join(
            f"{v}={i}" for v, i in self.venue_to_idx.items()
        )
        self.idata.attrs["asof_date"] = self.asof_date.isoformat()
        self.idata.attrs["lookback_years"] = self.lookback_years
        self.idata.attrs["dropped_teams"] = "|".join(self.dropped_teams)
        self.idata.to_netcdf(str(path))

    @classmethod
    def load(cls, path: str | Path) -> BayesianModel:
        idata = az.from_netcdf(str(path))

        def _parse_map(s: str) -> dict[str, int]:
            if not s:
                return {}
            out: dict[str, int] = {}
            for kv in s.split(","):
                k, v = kv.rsplit("=", 1)
                out[k] = int(v)
            return out

        return cls(
            idata=idata,
            team_to_idx=_parse_map(idata.attrs.get("team_to_idx", "")),
            venue_to_idx=_parse_map(idata.attrs.get("venue_to_idx", "")),
            asof_date=date.fromisoformat(idata.attrs["asof_date"]),
            lookback_years=int(idata.attrs.get("lookback_years", 4)),
            dropped_teams=[t for t in idata.attrs.get("dropped_teams", "").split("|") if t],
        )


@dataclass
class BayesianPrediction:
    home_team: str
    away_team: str
    venue_country: str | None
    p_home_win: float
    p_draw: float
    p_away_win: float
    expected_home_goals: float
    expected_away_goals: float
    score_matrix: np.ndarray

    def asdict(self) -> dict:
        return {
            "home_team": self.home_team,
            "away_team": self.away_team,
            "venue_country": self.venue_country,
            "p_home_win": self.p_home_win,
            "p_draw": self.p_draw,
            "p_away_win": self.p_away_win,
            "expected_home_goals": self.expected_home_goals,
            "expected_away_goals": self.expected_away_goals,
        }


def _to_date(x: date | str | datetime) -> date:
    if isinstance(x, date) and not isinstance(x, datetime):
        return x
    if isinstance(x, datetime):
        return x.date()
    return datetime.fromisoformat(str(x)).date()


def _prepare(
    matches: pd.DataFrame,
    asof_date: date,
    lookback_years: int,
    min_team_matches: int,
) -> tuple[pd.DataFrame, dict[str, int], dict[str, int], list[str]]:
    df = matches.copy()
    df["date"] = pd.to_datetime(df["date"]).dt.date
    cutoff_lo = date(asof_date.year - lookback_years, asof_date.month, asof_date.day)
    df = df[(df["date"] >= cutoff_lo) & (df["date"] < asof_date)]
    df = df.dropna(subset=["home_goals", "away_goals"]).copy()

    counts = pd.concat([df["home_team"], df["away_team"]]).value_counts()
    keep = set(counts[counts >= min_team_matches].index)
    all_teams = set(counts.index)
    dropped = sorted(all_teams - keep)
    df = df[df["home_team"].isin(keep) & df["away_team"].isin(keep)].copy()
    if df.empty:
        raise ValueError(f"No training matches in [{cutoff_lo}, {asof_date})")

    df["venue_country"] = df["venue_country"].fillna("__neutral__").astype(str)

    teams = sorted(set(df["home_team"]).union(df["away_team"]))
    venues = sorted(df["venue_country"].unique())
    t2i = {t: i for i, t in enumerate(teams)}
    v2i = {v: i for i, v in enumerate(venues)}

    df["home_idx"] = df["home_team"].map(t2i).astype(int)
    df["away_idx"] = df["away_team"].map(t2i).astype(int)
    df["venue_idx"] = df["venue_country"].map(v2i).astype(int)
    df["home_goals"] = df["home_goals"].astype(int)
    df["away_goals"] = df["away_goals"].astype(int)
    return df, t2i, v2i, dropped


def _build_model(
    df: pd.DataFrame,
    team_to_idx: dict[str, int],
    venue_to_idx: dict[str, int],
) -> pm.Model:
    n_teams = len(team_to_idx)
    n_venues = len(venue_to_idx)

    home_idx = df["home_idx"].to_numpy()
    away_idx = df["away_idx"].to_numpy()
    venue_idx = df["venue_idx"].to_numpy()
    hg = df["home_goals"].to_numpy()
    ag = df["away_goals"].to_numpy()

    # Per-venue host prior: shape (n_venues,). Looked up by venue country name.
    venue_country_names = [v for v, _ in sorted(venue_to_idx.items(), key=lambda kv: kv[1])]
    host_prior_mu = np.array([HOST_PRIORS.get(v, DEFAULT_HOST_PRIOR) for v in venue_country_names])

    with pm.Model() as model:
        mu = pm.Normal("mu", mu=0.0, sigma=1.0)

        sigma_att = pm.HalfNormal("sigma_att", sigma=1.0)
        sigma_def = pm.HalfNormal("sigma_def", sigma=1.0)

        att_raw = pm.Normal("att_raw", mu=0.0, sigma=sigma_att, shape=n_teams)
        def_raw = pm.Normal("def_raw", mu=0.0, sigma=sigma_def, shape=n_teams)
        # Sum-to-zero via centering — standard identifiability fix.
        att = pm.Deterministic("att", att_raw - att_raw.mean())
        def_ = pm.Deterministic("def_", def_raw - def_raw.mean())

        sigma_gamma = pm.HalfNormal("sigma_gamma", sigma=0.5)
        # γ[team, venue]: full (n_teams, n_venues) is large; we model as additive
        # team-agnostic venue effect centered on host prior, plus team×venue noise.
        gamma_venue = pm.Normal("gamma_venue", mu=host_prior_mu, sigma=sigma_gamma, shape=n_venues)

        log_lambda_home = mu + att[home_idx] + def_[away_idx] + gamma_venue[venue_idx]
        log_lambda_away = mu + att[away_idx] + def_[home_idx]

        pm.Poisson("home_goals", mu=pm.math.exp(log_lambda_home), observed=hg)
        pm.Poisson("away_goals", mu=pm.math.exp(log_lambda_away), observed=ag)

    return model


def fit(
    matches: pd.DataFrame,
    asof_date: date | str,
    lookback_years: int = 4,
    draws: int = 1500,
    tune: int = 1500,
    chains: int = 4,
    target_accept: float = 0.95,
    min_team_matches: int = 5,
    fast: bool = False,
    random_seed: int = 42,
) -> BayesianModel:
    """Fit hierarchical Bayesian Poisson model on matches strictly before `asof_date`.

    `fast=True` uses pm.find_MAP() and wraps the point estimate in an InferenceData with a
    single posterior draw — useful for CI / smoke tests where full NUTS is too slow.
    """
    asof = _to_date(asof_date)
    df, t2i, v2i, dropped = _prepare(matches, asof, lookback_years, min_team_matches)
    model = _build_model(df, t2i, v2i)

    with model:
        if fast:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                point = pm.find_MAP(progressbar=False)
            posterior = {}
            for k, v in point.items():
                arr = np.asarray(v)
                posterior[k] = arr[None, None, ...]  # (chain=1, draw=1, *shape)
            idata = az.from_dict(posterior=posterior)
        else:
            idata = pm.sample(
                draws=draws,
                tune=tune,
                chains=chains,
                target_accept=target_accept,
                random_seed=random_seed,
                progressbar=False,
                idata_kwargs={"log_likelihood": False},
            )

    return BayesianModel(
        idata=idata,
        team_to_idx=t2i,
        venue_to_idx=v2i,
        asof_date=asof,
        lookback_years=lookback_years,
        dropped_teams=dropped,
    )


def _posterior_array(idata: az.InferenceData, name: str) -> np.ndarray:
    """Flatten (chain, draw, ...) → (samples, ...)."""
    da = idata.posterior[name]
    arr = da.values
    return arr.reshape(-1, *arr.shape[2:])


def predict(
    model: BayesianModel,
    home_team: str,
    away_team: str,
    venue_country: str | None = None,
    max_goals: int = 10,
) -> BayesianPrediction:
    if home_team not in model.team_to_idx:
        raise KeyError(f"Unknown home team: {home_team}")
    if away_team not in model.team_to_idx:
        raise KeyError(f"Unknown away team: {away_team}")

    h = model.team_to_idx[home_team]
    a = model.team_to_idx[away_team]

    mu = _posterior_array(model.idata, "mu")  # (S,)
    att = _posterior_array(model.idata, "att")  # (S, n_teams)
    def_ = _posterior_array(model.idata, "def_")  # (S, n_teams)
    gamma_venue = _posterior_array(model.idata, "gamma_venue")  # (S, n_venues)

    if venue_country is not None and venue_country in model.venue_to_idx:
        v_idx = model.venue_to_idx[venue_country]
        gamma_h = gamma_venue[:, v_idx]
    elif venue_country is not None and venue_country in HOST_PRIORS:
        # Unseen but known WC2026 host country — fall back to host prior point.
        gamma_h = np.full(mu.shape, HOST_PRIORS[venue_country])
    else:
        gamma_h = gamma_venue.mean(axis=1)

    lam_h = np.exp(mu + att[:, h] + def_[:, a] + gamma_h)  # (S,)
    lam_a = np.exp(mu + att[:, a] + def_[:, h])  # (S,)

    g = np.arange(max_goals + 1)
    # Poisson pmf per sample, vectorized.
    # log_pmf_h[s, k] = -lam_h[s] + k*log(lam_h[s]) - lgamma(k+1)
    from scipy.special import gammaln

    log_lh = -lam_h[:, None] + g[None, :] * np.log(lam_h[:, None] + 1e-12) - gammaln(g + 1)[None, :]
    log_la = -lam_a[:, None] + g[None, :] * np.log(lam_a[:, None] + 1e-12) - gammaln(g + 1)[None, :]
    pmf_h = np.exp(log_lh)  # (S, G+1)
    pmf_a = np.exp(log_la)
    # Score matrix per sample, then average — integrates over posterior uncertainty.
    score = np.einsum("si,sj->ij", pmf_h, pmf_a) / pmf_h.shape[0]
    score /= score.sum()

    p_home = float(np.tril(score, k=-1).sum())
    p_draw = float(np.trace(score))
    p_away = float(np.triu(score, k=1).sum())
    eh = float((g[:, None] * score).sum())
    ea = float((g[None, :] * score).sum())

    return BayesianPrediction(
        home_team=home_team,
        away_team=away_team,
        venue_country=venue_country,
        p_home_win=p_home,
        p_draw=p_draw,
        p_away_win=p_away,
        expected_home_goals=eh,
        expected_away_goals=ea,
        score_matrix=score,
    )


def predict_many(model: BayesianModel, fixtures: pd.DataFrame, max_goals: int = 10) -> pd.DataFrame:
    rows = []
    for r in fixtures.itertuples(index=False):
        h = r.home_team
        a = r.away_team
        vc = getattr(r, "venue_country", None)
        try:
            rows.append(predict(model, h, a, venue_country=vc, max_goals=max_goals).asdict())
        except Exception as exc:
            rows.append({"home_team": h, "away_team": a, "venue_country": vc, "error": str(exc)})
    return pd.DataFrame(rows)


def _cli() -> int:
    p = argparse.ArgumentParser(description="Fit hierarchical Bayesian goal model.")
    p.add_argument("--fit", action="store_true")
    p.add_argument("--asof", required=True, help="YYYY-MM-DD cutoff (strict <).")
    p.add_argument("--matches", default="data/processed/matches.parquet")
    p.add_argument("--out", required=True)
    p.add_argument("--lookback-years", type=int, default=4)
    p.add_argument("--draws", type=int, default=1500)
    p.add_argument("--tune", type=int, default=1500)
    p.add_argument("--chains", type=int, default=4)
    p.add_argument("--target-accept", type=float, default=0.95)
    p.add_argument("--fast", action="store_true", help="Use pm.find_MAP() instead of NUTS.")
    args = p.parse_args()

    if not args.fit:
        p.error("--fit required")

    matches = pd.read_parquet(args.matches)
    t0 = datetime.now()
    model = fit(
        matches,
        asof_date=args.asof,
        lookback_years=args.lookback_years,
        draws=args.draws,
        tune=args.tune,
        chains=args.chains,
        target_accept=args.target_accept,
        fast=args.fast,
    )
    dt = (datetime.now() - t0).total_seconds()
    model.save(args.out)
    print(
        f"Fit complete in {dt:.1f}s. teams={len(model.team_to_idx)} dropped={len(model.dropped_teams)}"
    )
    print(f"Saved → {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
