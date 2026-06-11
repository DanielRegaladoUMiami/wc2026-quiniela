"""Strategy: convert probabilistic model output to optimal pool entries."""

# NOTE: make_quiniela is intentionally NOT re-exported here — it is a CLI module
# (`python -m src.strategy.make_quiniela`) and importing it at package level
# triggers runpy's double-import warning.
from .bracket_picks import BracketPick, normalize_advancement, pick_bracket
from .optimize_entries import Entry, optimize_entries
from .pool_ev import (
    Rubric,
    best_1x2_pick,
    best_exact_score_pick,
    best_fifa_mx_pick,
    expected_points,
    load_rubric,
    score_matrix_to_dist,
)
from .public_estimator import estimate_public_champion, estimate_public_picks

__all__ = [
    "BracketPick",
    "Entry",
    "Rubric",
    "best_1x2_pick",
    "best_exact_score_pick",
    "best_fifa_mx_pick",
    "estimate_public_champion",
    "estimate_public_picks",
    "expected_points",
    "load_rubric",
    "normalize_advancement",
    "optimize_entries",
    "pick_bracket",
    "score_matrix_to_dist",
]
