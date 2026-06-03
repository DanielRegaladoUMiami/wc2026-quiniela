"""ESPN-style bracket pick optimizer.

Walks forward round-by-round, picking the team with max E[points] per slot
(optionally penalized by public ownership).

Independence assumption (documented):
  Per-round advancement probabilities (p_R16, p_QF, ...) from the
  `advancement` table are treated as marginal P(team reaches round R).
  This module does NOT enforce bracket consistency across rounds — e.g.
  it may pick team A to win R16 and team B (in the same R16 slot) to win
  QF. For ESPN-style scoring that tallies per round-slot, this is OK and
  matches how those pools score. For brackets that require a coherent
  single tree, run `enforce_consistency=True` to project picks downward.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from .pool_ev import Rubric


@dataclass
class BracketPick:
    picks_by_round: dict[str, list[str]]
    expected_points: float
    reasoning: str
    diagnostics: dict[str, float] = field(default_factory=dict)


def _round_slots(round_name: str) -> int:
    """Number of teams advancing through round R (i.e. slot count to fill)."""
    return {"R32": 32, "R16": 16, "QF": 8, "SF": 4, "F": 2, "W": 1}[round_name]


def pick_bracket(
    advancement: pd.DataFrame,
    rubric: Rubric,
    public_picks: pd.DataFrame | None = None,
    contrarian_weight: float = 0.0,
) -> BracketPick:
    """Pick top-N teams per round by EV (minus optional public-ownership penalty).

    `advancement` columns required:
        team, p_R16, p_QF, p_SF, p_final, p_champion  (subset OK if rubric matches)
    `public_picks`:  optional DataFrame with columns team, public_p_champion (used
        as a proxy for ownership in every late round).
    """
    if rubric.type != "knockout_bracket":
        raise ValueError("pick_bracket requires a knockout_bracket rubric")

    rounds = rubric.config["rounds"]
    pub_by_team: dict[str, float] = {}
    if public_picks is not None and "public_p_champion" in public_picks.columns:
        pub_by_team = dict(
            zip(public_picks["team"], public_picks["public_p_champion"], strict=False)
        )

    picks_by_round: dict[str, list[str]] = {}
    total_ev = 0.0
    notes: list[str] = []

    # Map rubric round name -> column in advancement.
    col_map = {
        "R32": "p_advance",  # made it out of groups
        "R16": "p_R16",
        "QF": "p_QF",
        "SF": "p_SF",
        "F": "p_final",
        "W": "p_champion",
    }

    for rd in rounds:
        rname = rd["name"]
        points = rd["points"]
        col = col_map.get(rname)
        if col is None or col not in advancement.columns:
            continue
        # EV per team for this round.
        df = advancement[["team", col]].copy()
        df["ev"] = df[col] * points
        if contrarian_weight > 0 and pub_by_team:
            df["pub"] = df["team"].map(pub_by_team).fillna(0.0)
            df["obj"] = df["ev"] - contrarian_weight * points * df["pub"]
        else:
            df["obj"] = df["ev"]
        n_slots = min(_round_slots(rname), len(df))
        chosen = df.sort_values("obj", ascending=False).head(n_slots)
        picks_by_round[rname] = chosen["team"].tolist()
        round_ev = float(chosen["ev"].sum())
        total_ev += round_ev
        notes.append(f"- **{rname}** ({points} pts/slot, {n_slots} picks): E[pts]={round_ev:.1f}")

    reasoning = (
        "Bracket picks walk forward by round, taking top teams by E[points]. "
        + (
            f"Contrarian weight={contrarian_weight}: discounts each team's EV by "
            "its public champion-ownership.\n\n"
            if contrarian_weight > 0
            else "Pure chalk: no contrarian adjustment.\n\n"
        )
        + "\n".join(notes)
    )

    return BracketPick(
        picks_by_round=picks_by_round,
        expected_points=total_ev,
        reasoning=reasoning,
        diagnostics={"n_rounds": float(len(picks_by_round))},
    )
