"""Pool EV: rubric loading + expected-points calculators.

All functions are pure: predictions in, scalars / picks out.

Assumption everywhere: any `score_matrix` passed in is shape (M+1, M+1)
with entry [i, j] = P(home scores i, away scores j), normalized so the
matrix sums to 1.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import yaml

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

Pick = Any  # e.g. "H" | (i, j) | "BRA"
Outcome = Any
ScoreFn = Callable[[Pick, Outcome], int]


@dataclass(frozen=True)
class Rubric:
    """Generic rubric. `score_function(pick, actual) -> int`."""

    name: str
    type: str
    score_function: ScoreFn
    config: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Score functions per rubric type
# ---------------------------------------------------------------------------


def _result_1x2(home_goals: int, away_goals: int) -> str:
    if home_goals > away_goals:
        return "H"
    if home_goals < away_goals:
        return "A"
    return "D"


def _score_fifa_quiniela_mx(cfg: dict[str, Any]) -> ScoreFn:
    pts_1x2 = next(f["points_correct"] for f in cfg["fields"] if f["name"] == "result_1x2")
    totals_cfg = next(f for f in cfg["fields"] if f["name"] == "totals")
    pts_tot = totals_cfg["points_correct"]
    thr = float(totals_cfg["threshold"])

    def score(pick: tuple[str, str], actual: tuple[int, int]) -> int:
        pick_1x2, pick_tot = pick
        h, a = actual
        pts = 0
        if pick_1x2 == _result_1x2(h, a):
            pts += pts_1x2
        actual_tot = "OVER" if (h + a) > thr else "UNDER"
        if pick_tot == actual_tot:
            pts += pts_tot
        return pts

    return score


def _score_exact_score(cfg: dict[str, Any]) -> ScoreFn:
    pe = cfg["points"]["exact"]
    pgd = cfg["points"]["gd_and_winner"]
    pw = cfg["points"]["winner_only"]

    def score(pick: tuple[int, int], actual: tuple[int, int]) -> int:
        ph, pa = pick
        ah, aa = actual
        if ph == ah and pa == aa:
            return pe
        pick_res = _result_1x2(ph, pa)
        act_res = _result_1x2(ah, aa)
        if pick_res != act_res:
            return 0
        if (ph - pa) == (ah - aa):
            return pgd
        return pw

    return score


def _score_bracket(cfg: dict[str, Any]) -> ScoreFn:
    """Score one team-in-round pick. pick=team, actual=team that reached round."""
    # Used for per-round scoring; per-round point value is looked up by caller.
    _ = cfg

    def score(pick: str, actual: str) -> int:
        return 1 if pick == actual else 0

    return score


_SCORE_BUILDERS: dict[str, Callable[[dict[str, Any]], ScoreFn]] = {
    "composite_1x2_totals": _score_fifa_quiniela_mx,
    "exact_score_tiered": _score_exact_score,
    "knockout_bracket": _score_bracket,
}


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------


def load_rubric(path: str | Path) -> Rubric:
    cfg = yaml.safe_load(Path(path).read_text())
    rtype = cfg["type"]
    if rtype not in _SCORE_BUILDERS:
        raise ValueError(f"unknown rubric type: {rtype}")
    return Rubric(
        name=cfg["name"],
        type=rtype,
        score_function=_SCORE_BUILDERS[rtype](cfg),
        config=cfg,
    )


# ---------------------------------------------------------------------------
# Expected points
# ---------------------------------------------------------------------------


def expected_points(
    pick: Pick,
    prob_dist: dict[Outcome, float],
    rubric: Rubric,
) -> float:
    """Generic E[points] = Σ_o P(o) · rubric(pick, o)."""
    return float(sum(p * rubric.score_function(pick, o) for o, p in prob_dist.items()))


# ---------- specific helpers --------------------------------------------------


def score_matrix_to_dist(score_matrix: np.ndarray) -> dict[tuple[int, int], float]:
    """Convert (M+1, M+1) P(home=i, away=j) matrix into a dict outcome→prob."""
    return {
        (i, j): float(score_matrix[i, j])
        for i in range(score_matrix.shape[0])
        for j in range(score_matrix.shape[1])
        if score_matrix[i, j] > 0.0
    }


def best_exact_score_pick(
    score_matrix: np.ndarray, rubric: Rubric
) -> tuple[tuple[int, int], float]:
    """Enumerate all (i,j) in [0..max]² and pick the one maximizing E[points]."""
    max_g = int(rubric.config.get("max_goals", score_matrix.shape[0] - 1))
    dist = score_matrix_to_dist(score_matrix)
    best_pick = (0, 0)
    best_ev = -np.inf
    for i in range(max_g + 1):
        for j in range(max_g + 1):
            ev = expected_points((i, j), dist, rubric)
            if ev > best_ev:
                best_ev = ev
                best_pick = (i, j)
    return best_pick, float(best_ev)


def best_1x2_pick(p_home: float, p_draw: float, p_away: float, rubric: Rubric) -> tuple[str, float]:
    """Best 1X2 pick under any rubric whose actual-outcome is a (h,a) tuple."""
    # Marginalize via representative outcomes since 1X2 is winner-only here.
    dist_by_res = {"H": p_home, "D": p_draw, "A": p_away}
    candidates: Iterable[str] = ("H", "D", "A")

    def res_to_actual(r: str) -> tuple[int, int]:
        return {"H": (1, 0), "D": (0, 0), "A": (0, 1)}[r]

    best_pick, best_ev = "H", -np.inf
    for c in candidates:
        ev = sum(
            p * rubric.score_function((c, "UNDER"), res_to_actual(r))
            for r, p in dist_by_res.items()
        )
        if ev > best_ev:
            best_pick, best_ev = c, ev
    return best_pick, float(best_ev)


def best_fifa_mx_pick(score_matrix: np.ndarray, rubric: Rubric) -> tuple[tuple[str, str], float]:
    """Joint best pick (1X2, OVER/UNDER) for the Mexican composite rubric."""
    dist = score_matrix_to_dist(score_matrix)
    best_pick: tuple[str, str] = ("H", "UNDER")
    best_ev = -np.inf
    for r in ("H", "D", "A"):
        for t in ("OVER", "UNDER"):
            ev = expected_points((r, t), dist, rubric)
            if ev > best_ev:
                best_ev = ev
                best_pick = (r, t)
    return best_pick, float(best_ev)


# ---------------------------------------------------------------------------
# Bracket EV
# ---------------------------------------------------------------------------
#
# Independence assumption (documented):
#   We assume P(team T reaches round R) values from the `advancement` table
#   are marginal and we treat per-round picks as independent for EV purposes.
#   This is wrong in joint reality (if team T loses in R16, it cannot be the
#   champion) but is a standard simplification — we score each round-slot
#   independently with the round's point value, which matches how ESPN-style
#   pools tally.


def bracket_round_ev(
    team: str,
    round_name: str,
    advancement_row_lookup: dict[str, dict[str, float]],
    round_points: int,
) -> float:
    """E[points] for picking `team` to reach `round_name`."""
    p = advancement_row_lookup.get(team, {}).get(f"p_{round_name}", 0.0)
    return float(p * round_points)
