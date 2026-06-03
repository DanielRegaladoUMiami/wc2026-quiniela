"""Build N pool entries: 1 chalk + 1 moderate contrarian + 1 high-variance.

Entry = a full set of picks across all matches in the pool.

Strategy per entry:
  * chalk:       maximize raw E[points]
  * moderate:    maximize  E[points] - λ * public_overlap_prob
  * high-var:    same as moderate but only deviate from chalk where the EV
                 gap is below a threshold (so we pick the contrarian only
                 when the price is small).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .pool_ev import (
    Rubric,
    expected_points,
    score_matrix_to_dist,
)


@dataclass
class Entry:
    picks: pd.DataFrame
    expected_points: float
    expected_pool_rank_pct: float
    reasoning: str
    label: str = ""
    diagnostics: dict[str, float] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Per-match candidate enumeration
# ---------------------------------------------------------------------------


def _enumerate_1x2(row: pd.Series, rubric: Rubric) -> list[tuple[str, float]]:
    """Return list[(pick, EV)] for the 3 possible 1X2 picks."""
    out = []
    for cand in ("H", "D", "A"):
        # Reuse best_1x2_pick by forcing the pick.
        actual_map = {"H": (1, 0), "D": (0, 0), "A": (0, 1)}
        ev = (
            row["p_home_win"] * rubric.score_function((cand, "UNDER"), actual_map["H"])
            + row["p_draw"] * rubric.score_function((cand, "UNDER"), actual_map["D"])
            + row["p_away_win"] * rubric.score_function((cand, "UNDER"), actual_map["A"])
        )
        out.append((cand, float(ev)))
    return out


def _enumerate_fifa_mx(row: pd.Series, rubric: Rubric) -> list[tuple[tuple[str, str], float]]:
    dist = score_matrix_to_dist(row["score_matrix"])
    out = []
    for r in ("H", "D", "A"):
        for t in ("OVER", "UNDER"):
            ev = expected_points((r, t), dist, rubric)
            out.append(((r, t), float(ev)))
    return out


def _enumerate_exact_score(row: pd.Series, rubric: Rubric) -> list[tuple[tuple[int, int], float]]:
    dist = score_matrix_to_dist(row["score_matrix"])
    max_g = int(rubric.config.get("max_goals", 5))
    out = []
    for i in range(max_g + 1):
        for j in range(max_g + 1):
            out.append(((i, j), float(expected_points((i, j), dist, rubric))))
    return out


def _candidates_for_match(row: pd.Series, rubric: Rubric) -> list[tuple[object, float]]:
    if rubric.type == "composite_1x2_totals":
        return _enumerate_fifa_mx(row, rubric)
    if rubric.type == "exact_score_tiered":
        return _enumerate_exact_score(row, rubric)
    # default: 1X2
    return _enumerate_1x2(row, rubric)


# ---------------------------------------------------------------------------
# Public-overlap probability for a pick
# ---------------------------------------------------------------------------


def _public_overlap(pick: object, public_row: pd.Series, rubric_type: str) -> float:
    """Approximate P(a public entry picks the same thing) for one match."""
    if rubric_type == "composite_1x2_totals":
        result, _totals = pick  # type: ignore[misc]
    else:
        # For exact-score and 1X2, derive the implied 1X2.
        if isinstance(pick, tuple) and len(pick) == 2 and isinstance(pick[0], int):
            i, j = pick  # type: ignore[misc]
            result = "H" if i > j else "A" if i < j else "D"
        else:
            result = pick  # already "H"/"D"/"A"
    return float(
        {
            "H": public_row["public_p_home"],
            "D": public_row["public_p_draw"],
            "A": public_row["public_p_away"],
        }[result]
    )


# ---------------------------------------------------------------------------
# Entry builders
# ---------------------------------------------------------------------------


def _pick_per_match(
    match_probs: pd.DataFrame,
    public_probs: pd.DataFrame,
    rubric: Rubric,
    lam: float,
    contrarian_only_if_gap_lt: float | None = None,
    chalk_picks: list[object] | None = None,
) -> tuple[list[object], list[float], list[float]]:
    """Returns (picks, evs, overlaps) per match."""
    picks: list[object] = []
    evs: list[float] = []
    overlaps: list[float] = []
    pub_idx = public_probs.set_index("match_num")
    for k, (_, row) in enumerate(match_probs.iterrows()):
        pub_row = pub_idx.loc[row["match_num"]]
        cands = _candidates_for_match(row, rubric)
        max(ev for _, ev in cands)
        scored = []
        for pick, ev in cands:
            ov = _public_overlap(pick, pub_row, rubric.type)
            obj = ev - lam * ov
            scored.append((obj, ev, ov, pick))
        scored.sort(reverse=True, key=lambda x: x[0])
        chosen = scored[0]

        if contrarian_only_if_gap_lt is not None and chalk_picks is not None:
            # If switching from chalk costs too much EV, fall back to chalk.
            chalk_pick = chalk_picks[k]
            chalk_match_ev = next(ev for p, ev in cands if p == chalk_pick)
            if (chalk_match_ev - chosen[1]) > contrarian_only_if_gap_lt:
                ov_chalk = _public_overlap(chalk_pick, pub_row, rubric.type)
                chosen = (chalk_match_ev - lam * ov_chalk, chalk_match_ev, ov_chalk, chalk_pick)

        picks.append(chosen[3])
        evs.append(chosen[1])
        overlaps.append(chosen[2])
    return picks, evs, overlaps


def _picks_df(match_probs: pd.DataFrame, picks: list[object], evs: list[float]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "match_num": match_probs["match_num"].values,
            "home_team": match_probs["home_team"].values,
            "away_team": match_probs["away_team"].values,
            "pick": picks,
            "ev": evs,
        }
    )


def _estimate_rank_pct(total_ev: float, total_overlap: float, n_matches: int) -> float:
    """Cheap heuristic: lower public-overlap + higher EV → better expected rank."""
    if n_matches == 0:
        return 0.5
    norm_ev = total_ev / max(1.0, n_matches)
    norm_ov = total_overlap / n_matches
    # Map roughly into (0, 1) where smaller is better.
    score = norm_ev - 2.0 * norm_ov
    # Squash via logistic-ish.
    return float(1.0 / (1.0 + np.exp(score)))


def optimize_entries(
    match_probs: pd.DataFrame,
    public_probs: pd.DataFrame,
    rubric: Rubric,
    n_entries: int = 3,
    diversity_weight: float = 0.3,
) -> list[Entry]:
    """Build N entries with chalk → moderate → high-variance contrarian profile."""
    if n_entries < 1:
        raise ValueError("n_entries must be >= 1")

    entries: list[Entry] = []

    # 1) Chalk entry.
    chalk_picks, chalk_evs, chalk_overlaps = _pick_per_match(
        match_probs, public_probs, rubric, lam=0.0
    )
    chalk_total = float(sum(chalk_evs))
    chalk_df = _picks_df(match_probs, chalk_picks, chalk_evs)
    entries.append(
        Entry(
            picks=chalk_df,
            expected_points=chalk_total,
            expected_pool_rank_pct=_estimate_rank_pct(
                chalk_total, float(sum(chalk_overlaps)), len(match_probs)
            ),
            reasoning=(
                "**Chalk entry**: maximizes E[points] per match independently. "
                "Best when pool is small or scoring rewards accuracy over differentiation."
            ),
            label="chalk",
            diagnostics={"total_overlap": float(sum(chalk_overlaps))},
        )
    )
    if n_entries == 1:
        return entries

    # 2) Moderate contrarian.
    mod_picks, mod_evs, mod_ov = _pick_per_match(
        match_probs, public_probs, rubric, lam=diversity_weight
    )
    mod_total = float(sum(mod_evs))
    n_diff_mod = sum(1 for a, b in zip(chalk_picks, mod_picks, strict=False) if a != b)
    entries.append(
        Entry(
            picks=_picks_df(match_probs, mod_picks, mod_evs),
            expected_points=mod_total,
            expected_pool_rank_pct=_estimate_rank_pct(
                mod_total, float(sum(mod_ov)), len(match_probs)
            ),
            reasoning=(
                f"**Moderate contrarian** (λ={diversity_weight}): swaps {n_diff_mod} "
                "match(es) toward EV-positive picks the public underweights. "
                "Trades a small E[points] hit for tail-rank upside in mid-sized pools."
            ),
            label="moderate_contrarian",
            diagnostics={"n_swapped_from_chalk": float(n_diff_mod)},
        )
    )
    if n_entries == 2:
        return entries

    # 3) High-variance contrarian: stronger λ but require gap < threshold.
    hv_lam = max(diversity_weight * 2.0, 0.6)
    hv_picks, hv_evs, hv_ov = _pick_per_match(
        match_probs,
        public_probs,
        rubric,
        lam=hv_lam,
        contrarian_only_if_gap_lt=0.25,
        chalk_picks=chalk_picks,
    )
    hv_total = float(sum(hv_evs))
    n_diff_hv = sum(1 for a, b in zip(chalk_picks, hv_picks, strict=False) if a != b)
    entries.append(
        Entry(
            picks=_picks_df(match_probs, hv_picks, hv_evs),
            expected_points=hv_total,
            expected_pool_rank_pct=_estimate_rank_pct(
                hv_total, float(sum(hv_ov)), len(match_probs)
            ),
            reasoning=(
                f"**High-variance contrarian** (λ={hv_lam}, gap≤0.25): swings only "
                f"on matches where the contrarian pick costs <0.25 EV; swapped "
                f"{n_diff_hv} match(es). Designed for large pools where rank "
                "differentiation dominates raw accuracy."
            ),
            label="high_variance",
            diagnostics={"n_swapped_from_chalk": float(n_diff_hv)},
        )
    )

    # Additional entries: random-ish further contrarian via increasing λ.
    extra_idx = 0
    while len(entries) < n_entries:
        extra_idx += 1
        lam = diversity_weight + 0.15 * extra_idx
        picks, evs_, ov = _pick_per_match(match_probs, public_probs, rubric, lam=lam)
        total = float(sum(evs_))
        entries.append(
            Entry(
                picks=_picks_df(match_probs, picks, evs_),
                expected_points=total,
                expected_pool_rank_pct=_estimate_rank_pct(total, float(sum(ov)), len(match_probs)),
                reasoning=f"**Extra contrarian #{extra_idx}** (λ={lam:.2f}).",
                label=f"extra_{extra_idx}",
            )
        )
    return entries
