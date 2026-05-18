"""Estimate the distribution of public picks.

The public is a blend of:
  - "sharp" money — well approximated by market-implied probabilities
  - "square" money — picks the favorite to win, no draws, no contrarian view

This module produces a public-pick probability per match (and per team for
brackets), used downstream to estimate contrarian edge.
"""

from __future__ import annotations

import pandas as pd

# ---------------------------------------------------------------------------
# Per-match public estimator
# ---------------------------------------------------------------------------


def _square_picks_from_model(match_probs: pd.DataFrame) -> pd.DataFrame:
    """Square money = always pick the modal 1X2 outcome with full mass."""
    out = []
    for _, r in match_probs.iterrows():
        ph, pa = r["p_home_win"], r["p_away_win"]
        # Square bettors avoid the draw — collapse it onto the favorite side.
        if ph >= pa:
            out.append((1.0, 0.0, 0.0))
        else:
            out.append((0.0, 0.0, 1.0))
    sq = pd.DataFrame(out, columns=["public_p_home", "public_p_draw", "public_p_away"])
    sq.insert(0, "match_num", match_probs["match_num"].values)
    return sq


def estimate_public_picks(
    match_probs: pd.DataFrame,
    market_probs: pd.DataFrame | None = None,
    square_money_weight: float = 0.5,
) -> pd.DataFrame:
    """Return per-match public pick probabilities.

    Blend:
        public = (1 - w_sq) * market + w_sq * square
    If `market_probs` is None, use `match_probs` as the sharp prior.
    """
    if not 0.0 <= square_money_weight <= 1.0:
        raise ValueError("square_money_weight must be in [0, 1]")

    sharp_src = market_probs if market_probs is not None else match_probs
    sharp = sharp_src[["match_num", "p_home_win", "p_draw", "p_away_win"]].rename(
        columns={
            "p_home_win": "public_p_home",
            "p_draw": "public_p_draw",
            "p_away_win": "public_p_away",
        }
    )
    square = _square_picks_from_model(match_probs)

    merged = sharp.merge(square, on="match_num", suffixes=("_sharp", "_sq"))
    w = square_money_weight
    out = pd.DataFrame(
        {
            "match_num": merged["match_num"],
            "public_p_home": (1 - w) * merged["public_p_home_sharp"]
            + w * merged["public_p_home_sq"],
            "public_p_draw": (1 - w) * merged["public_p_draw_sharp"]
            + w * merged["public_p_draw_sq"],
            "public_p_away": (1 - w) * merged["public_p_away_sharp"]
            + w * merged["public_p_away_sq"],
        }
    )
    return out


# ---------------------------------------------------------------------------
# Bracket public estimator
# ---------------------------------------------------------------------------


def estimate_public_champion(
    advancement: pd.DataFrame,
    market_champion: pd.DataFrame | None = None,
    square_money_weight: float = 0.5,
    fifa_rank: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Blend market champion odds with a 'top-FIFA-rank per group' heuristic.

    Returns columns: team, public_p_champion.
    """
    sharp_src = market_champion if market_champion is not None else advancement
    sharp = sharp_src[["team", "p_champion"]].copy()
    sharp = sharp.rename(columns={"p_champion": "sharp"})

    if fifa_rank is not None and "group" in fifa_rank.columns:
        # Square money — concentrate champion mass on top-ranked team per group.
        best = fifa_rank.sort_values("fifa_rank").groupby("group").head(1)
        square = pd.DataFrame({"team": best["team"], "sq": 1.0 / len(best)})
    else:
        # Fallback: square mass proportional to (1 / position in sorted sharp).
        ranked = sharp.sort_values("sharp", ascending=False).reset_index(drop=True)
        ranked["sq"] = 0.0
        # Squares overweight top ~8 favorites.
        top = min(8, len(ranked))
        ranked.loc[: top - 1, "sq"] = 1.0 / top
        square = ranked[["team", "sq"]]

    merged = sharp.merge(square, on="team", how="left").fillna({"sq": 0.0})
    w = square_money_weight
    merged["public_p_champion"] = (1 - w) * merged["sharp"] + w * merged["sq"]
    # Renormalize to sum 1.
    s = merged["public_p_champion"].sum()
    if s > 0:
        merged["public_p_champion"] = merged["public_p_champion"] / s
    return merged[["team", "public_p_champion"]]
