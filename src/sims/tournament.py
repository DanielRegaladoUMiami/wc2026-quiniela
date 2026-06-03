"""Monte Carlo simulator for the FIFA World Cup 2026 bracket.

Accepts any predictor `predict(home, away) -> np.ndarray` returning a joint score-matrix
P(i,j) of shape (max_g+1, max_g+1). Dixon-Coles, Bayesian, LightGBM, and stackers all
satisfy this interface.

Caveat: FIFA's exact lookup table for assigning the 8 best third-placed teams to the 8
R32 slots is governed by a published 12-choose-8 regulations PDF that is NOT yet loaded
into `data/fixtures/third_placed_lookup.yaml`. Until then we approximate by uniformly
sampling (without replacement) one of the listed candidate groups for each placeholder
slot of the form "3X/Y/Z/...". This introduces bias of order ~1 R32 fixture per sim and
must be replaced before publishing official probabilities. TODO: load real lookup.
"""

from __future__ import annotations

import argparse
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.sims.bracket_2026 import GROUP_MATCHES, GROUPS, KNOCKOUT_FIXTURES
from src.sims.penalties import simulate_shootout

PredictFn = Callable[[str, str], np.ndarray]
StrengthFn = Callable[[str], float]

STAGES_ORDER = ["group", "R32", "R16", "QF", "SF", "final", "champion"]


@dataclass
class SimResults:
    advancement: pd.DataFrame
    match_probs: pd.DataFrame
    sample_brackets: pd.DataFrame
    n_sims: int
    seconds: float
    out_dir: Path | None = None


@dataclass
class _PredictorCache:
    """Caches score matrices and flattened cum-distributions per (home, away)."""

    predict_fn: PredictFn
    cache: dict[tuple[str, str], tuple[np.ndarray, np.ndarray, int]] = field(default_factory=dict)

    def get(self, home: str, away: str) -> tuple[np.ndarray, np.ndarray, int]:
        key = (home, away)
        hit = self.cache.get(key)
        if hit is not None:
            return hit
        sm = self.predict_fn(home, away)
        sm = np.asarray(sm, dtype=np.float64)
        sm = sm / sm.sum()
        flat = sm.ravel()
        cum = np.cumsum(flat)
        cum[-1] = 1.0
        dim = sm.shape[0]
        out = (sm, cum, dim)
        self.cache[key] = out
        return out


class TournamentSim:
    def __init__(
        self,
        predict_fn: PredictFn,
        strength_fn: StrengthFn | None = None,
    ) -> None:
        self.predict_fn = predict_fn
        self.strength_fn = strength_fn or (lambda _t: 0.0)
        self._cache = _PredictorCache(predict_fn)

    # ---- match sampling ---------------------------------------------------

    def simulate_match(
        self,
        home: str,
        away: str,
        rng: np.random.Generator,
        knockout: bool = False,
    ) -> tuple[int, int, str]:
        _sm, cum, dim = self._cache.get(home, away)
        idx = int(np.searchsorted(cum, rng.random(), side="right"))
        hg, ag = divmod(idx, dim)
        if not knockout:
            if hg > ag:
                winner = home
            elif ag > hg:
                winner = away
            else:
                winner = "draw"
            return hg, ag, winner
        if hg != ag:
            return hg, ag, home if hg > ag else away
        # tie -> shootout
        s_home = self.strength_fn(home)
        s_away = self.strength_fn(away)
        winner = home if simulate_shootout(s_home, s_away, rng) == 0 else away
        return hg, ag, winner

    # ---- group stage ------------------------------------------------------

    def simulate_group(
        self,
        group_letter: str,
        teams: list[str],
        rng: np.random.Generator,
    ) -> pd.DataFrame:
        matches = [m for m in GROUP_MATCHES if m["group"] == group_letter]
        results: list[tuple[str, str, int, int]] = []
        agg = {t: {"PTS": 0, "GF": 0, "GA": 0, "GD": 0} for t in teams}
        for m in matches:
            h, a = m["home"], m["away"]
            hg, ag, _ = self.simulate_match(h, a, rng, knockout=False)
            results.append((h, a, hg, ag))
            agg[h]["GF"] += hg
            agg[h]["GA"] += ag
            agg[a]["GF"] += ag
            agg[a]["GA"] += hg
            if hg > ag:
                agg[h]["PTS"] += 3
            elif ag > hg:
                agg[a]["PTS"] += 3
            else:
                agg[h]["PTS"] += 1
                agg[a]["PTS"] += 1
        for t in teams:
            agg[t]["GD"] = agg[t]["GF"] - agg[t]["GA"]
        df = pd.DataFrame([{"group": group_letter, "team": t, **agg[t]} for t in teams])
        return _apply_tiebreakers(df, results, rng)

    # ---- full tournament --------------------------------------------------

    def simulate_tournament(self, rng: np.random.Generator) -> dict[str, Any]:
        match_rows: list[dict] = []
        agg_by_group: dict[str, dict[str, dict[str, int]]] = {
            g: {t: {"PTS": 0, "GF": 0, "GA": 0, "GD": 0} for t in ts} for g, ts in GROUPS.items()
        }
        h2h_by_group: dict[str, list[tuple[str, str, int, int]]] = {g: [] for g in GROUPS}
        for m in GROUP_MATCHES:
            h, a = m["home"], m["away"]
            hg, ag, _ = self.simulate_match(h, a, rng, knockout=False)
            g = m["group"]
            agg_by_group[g][h]["GF"] += hg
            agg_by_group[g][h]["GA"] += ag
            agg_by_group[g][a]["GF"] += ag
            agg_by_group[g][a]["GA"] += hg
            if hg > ag:
                agg_by_group[g][h]["PTS"] += 3
            elif ag > hg:
                agg_by_group[g][a]["PTS"] += 3
            else:
                agg_by_group[g][h]["PTS"] += 1
                agg_by_group[g][a]["PTS"] += 1
            h2h_by_group[g].append((h, a, hg, ag))
            match_rows.append(
                {
                    "num": m["num"],
                    "stage": "group",
                    "home": h,
                    "away": a,
                    "home_goals": hg,
                    "away_goals": ag,
                    "winner": h if hg > ag else a if ag > hg else "draw",
                }
            )

        # finalize standings + tiebreakers (pure-Python; no DataFrames in hot path)
        position_map: dict[str, str] = {}
        standings_per_group: dict[str, list[tuple[str, int, int, int]]] = {}
        thirds: list[tuple[str, str, int, int, int]] = []
        for g, teams in GROUPS.items():
            rows: list[tuple[str, int, int, int]] = []
            for t in teams:
                a = agg_by_group[g][t]
                a["GD"] = a["GF"] - a["GA"]
                rows.append((t, a["PTS"], a["GD"], a["GF"]))
            ordered = _tiebreak_group(rows, h2h_by_group[g], rng)
            standings_per_group[g] = ordered
            position_map[f"1{g}"] = ordered[0][0]
            position_map[f"2{g}"] = ordered[1][0]
            position_map[f"3{g}"] = ordered[2][0]
            t3 = ordered[2]
            thirds.append((g, t3[0], t3[1], t3[2], t3[3]))

        # rank third-placed teams (PTS -> GD -> GF -> rng); take top 8
        thirds_sorted = sorted(thirds, key=lambda r: (-r[2], -r[3], -r[4], rng.random()))
        qualifying = thirds_sorted[:8]
        qualifying_groups = {r[0] for r in qualifying}
        third_team_by_group = {r[0]: r[1] for r in qualifying}

        # third-place placeholder assignment (approximation)
        ko_fixtures = [dict(m) for m in KNOCKOUT_FIXTURES]
        third_slots = [
            (i, m["away_pos"])
            for i, m in enumerate(ko_fixtures)
            if m["stage"] == "R32" and "/" in str(m["away_pos"])
        ]
        # Approximation: assign qualifying third-placed groups to slots uniformly
        # at random, respecting each slot's candidate group list.
        slot_assignment = _assign_thirds_to_slots(third_slots, qualifying_groups, rng)
        # slot_assignment: dict slot_index -> group_letter (one of qualifiers)

        # advancement tracker
        reached: dict[str, str] = {t: "group" for ts in GROUPS.values() for t in ts}
        for _g, ordered in standings_per_group.items():
            reached[ordered[0][0]] = "R32"
            reached[ordered[1][0]] = "R32"
        for g in qualifying_groups:
            reached[third_team_by_group[g]] = "R32"

        # resolve knockout fixtures
        winners: dict[int, str] = {}  # match num -> winner
        losers: dict[int, str] = {}
        stage_after: dict[str, str] = {
            "R32": "R16",
            "R16": "QF",
            "QF": "SF",
            "SF": "final",
            "final": "champion",
        }

        for idx, m in enumerate(ko_fixtures):
            home_pos = m["home_pos"]
            away_pos = m["away_pos"]
            home = _resolve_pos(
                home_pos, position_map, winners, losers, slot_assignment, idx, third_team_by_group
            )
            away = _resolve_pos(
                away_pos, position_map, winners, losers, slot_assignment, idx, third_team_by_group
            )
            if home is None or away is None:
                # missed third-placed (shouldn't happen if assignment succeeded)
                continue
            hg, ag, winner = self.simulate_match(home, away, rng, knockout=True)
            loser = away if winner == home else home
            winners[m["num"]] = winner
            losers[m["num"]] = loser
            match_rows.append(
                {
                    "num": m["num"],
                    "stage": m["stage"],
                    "home": home,
                    "away": away,
                    "home_goals": hg,
                    "away_goals": ag,
                    "winner": winner,
                }
            )
            # advancement
            if m["stage"] == "final":
                reached[winner] = "champion"
                # loser stays at "final"
                if reached.get(loser) != "champion":
                    reached[loser] = "final"
            elif m["stage"] != "3rd":
                nxt = stage_after[m["stage"]]
                if STAGES_ORDER.index(nxt) > STAGES_ORDER.index(reached.get(winner, "group")):
                    reached[winner] = nxt

        # third-place: the loser of 3rd-place match... but advancement P(3rd) means
        # winner of the 3rd-place fixture
        third_place_winner = winners.get(107)
        champion = winners.get(108, "UNKNOWN")

        return {
            "matches": match_rows,
            "advancement": reached,
            "champion": champion,
            "third_place_winner": third_place_winner,
            "standings": standings_per_group,
        }

    # ---- batch runner -----------------------------------------------------

    def run(
        self,
        n_sims: int = 50000,
        seed: int = 42,
        n_jobs: int = 1,
        out_root: Path | str = "data/sims",
        save: bool = True,
    ) -> SimResults:
        t0 = time.time()
        all_teams = [t for ts in GROUPS.values() for t in ts]
        team_idx = {t: i for i, t in enumerate(all_teams)}
        n_teams = len(all_teams)

        # stage counters: rows=teams, cols=stages
        stage_counts = np.zeros((n_teams, len(STAGES_ORDER)), dtype=np.int64)
        third_place_counts = np.zeros(n_teams, dtype=np.int64)
        champion_counts = np.zeros(n_teams, dtype=np.int64)

        # match-level: by match num
        all_match_nums = [m["num"] for m in GROUP_MATCHES] + [m["num"] for m in KNOCKOUT_FIXTURES]
        match_num_idx = {n: i for i, n in enumerate(sorted(all_match_nums))}
        n_matches = len(all_match_nums)
        # results: home_win, draw, away_win counts + accumulated goals
        mp = np.zeros((n_matches, 5), dtype=np.float64)  # hw, dw, aw, hg_sum, ag_sum
        # for knockout we don't have a fixed (home, away); we'll record by num
        mp_played = np.zeros(n_matches, dtype=np.int64)
        mp_home: list[str | None] = [None] * n_matches
        mp_away: list[str | None] = [None] * n_matches
        # group matches have fixed home/away
        for m in GROUP_MATCHES:
            i = match_num_idx[m["num"]]
            mp_home[i] = m["home"]
            mp_away[i] = m["away"]

        sample_brackets_rows: list[dict] = []

        master_rng = np.random.default_rng(seed)
        seeds = master_rng.integers(0, 2**63 - 1, size=n_sims)

        stage_idx_map = {s: i for i, s in enumerate(STAGES_ORDER)}
        for s_i in range(n_sims):
            rng = np.random.default_rng(seeds[s_i])
            out = self.simulate_tournament(rng)
            reached = out["advancement"]
            for t, stage in reached.items():
                stage_counts[team_idx[t], stage_idx_map[stage]] += 1
            ch = out["champion"]
            if ch in team_idx:
                champion_counts[team_idx[ch]] += 1
            tpw = out["third_place_winner"]
            if tpw in team_idx:
                third_place_counts[team_idx[tpw]] += 1
            for row in out["matches"]:
                i = match_num_idx[row["num"]]
                hg = row["home_goals"]
                ag = row["away_goals"]
                mp[i, 3] += hg
                mp[i, 4] += ag
                if hg > ag:
                    mp[i, 0] += 1
                elif ag > hg:
                    mp[i, 2] += 1
                else:
                    mp[i, 1] += 1
                mp_played[i] += 1

            if s_i < 100:
                for row in out["matches"]:
                    sample_brackets_rows.append({"sim_id": s_i, **row})

        # build advancement DataFrame with cumulative P(reach >= stage)
        # reached_stage is the FURTHEST stage. So P(reach R16) = sum of counts for R16 or later.
        cum = np.cumsum(stage_counts[:, ::-1], axis=1)[:, ::-1]
        # cum[:, k] = P(reach stage k or further) * n_sims
        prob = cum / n_sims
        adv_rows = []
        for t, i in team_idx.items():
            adv_rows.append(
                {
                    "team": t,
                    "p_advance_group": prob[i, STAGES_ORDER.index("R32")],
                    "p_R32_win": prob[i, STAGES_ORDER.index("R16")],
                    "p_R16_win": prob[i, STAGES_ORDER.index("QF")],
                    "p_QF_win": prob[i, STAGES_ORDER.index("SF")],
                    "p_SF_win": prob[i, STAGES_ORDER.index("final")],
                    "p_final_win": prob[i, STAGES_ORDER.index("champion")],
                    "p_champion": champion_counts[i] / n_sims,
                    "p_third_place": third_place_counts[i] / n_sims,
                }
            )
        adv_df = (
            pd.DataFrame(adv_rows).sort_values("p_champion", ascending=False).reset_index(drop=True)
        )

        # match probabilities
        mp_rows = []
        for num, i in match_num_idx.items():
            played = max(int(mp_played[i]), 1)
            mp_rows.append(
                {
                    "num": num,
                    "home": mp_home[i],
                    "away": mp_away[i],
                    "n_played": int(mp_played[i]),
                    "p_home_win": mp[i, 0] / played,
                    "p_draw": mp[i, 1] / played,
                    "p_away_win": mp[i, 2] / played,
                    "expected_home_goals": mp[i, 3] / played,
                    "expected_away_goals": mp[i, 4] / played,
                }
            )
        match_df = pd.DataFrame(mp_rows).sort_values("num").reset_index(drop=True)
        sample_df = pd.DataFrame(sample_brackets_rows)

        seconds = time.time() - t0
        out_dir = None
        if save:
            stamp = datetime.now().strftime("%Y%m%d%H%M")
            out_dir = Path(out_root) / f"sim_run_{stamp}"
            out_dir.mkdir(parents=True, exist_ok=True)
            adv_df.to_parquet(out_dir / "advancement.parquet", compression="zstd")
            match_df.to_parquet(out_dir / "match_probs.parquet", compression="zstd")
            if not sample_df.empty:
                sample_df.to_parquet(out_dir / "sample_brackets.parquet", compression="zstd")

        return SimResults(
            advancement=adv_df,
            match_probs=match_df,
            sample_brackets=sample_df,
            n_sims=n_sims,
            seconds=seconds,
            out_dir=out_dir,
        )


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------


def _tiebreak_group(
    rows: list[tuple[str, int, int, int]],
    h2h_results: list[tuple[str, str, int, int]],
    rng: np.random.Generator,
) -> list[tuple[str, int, int, int]]:
    """FIFA tiebreakers, pure-Python. rows = list of (team, PTS, GD, GF)."""
    # primary sort
    ordered = sorted(rows, key=lambda r: (-r[1], -r[2], -r[3]))
    # break (PTS,GD,GF) ties using H2H GD then rng
    out: list[tuple[str, int, int, int]] = []
    i = 0
    while i < len(ordered):
        j = i + 1
        while (
            j < len(ordered)
            and ordered[j][1] == ordered[i][1]
            and ordered[j][2] == ordered[i][2]
            and ordered[j][3] == ordered[i][3]
        ):
            j += 1
        block = ordered[i:j]
        if len(block) > 1:
            tied = {r[0] for r in block}
            h2h_gd = dict.fromkeys(tied, 0)
            for h, a, hg, ag in h2h_results:
                if h in tied and a in tied:
                    h2h_gd[h] += hg - ag
                    h2h_gd[a] += ag - hg
            block = sorted(block, key=lambda r: (-h2h_gd[r[0]], rng.random()))
        out.extend(block)
        i = j
    return out


def _apply_tiebreakers(
    df: pd.DataFrame,
    h2h_results: list[tuple[str, str, int, int]],
    rng: np.random.Generator,
) -> pd.DataFrame:
    """FIFA tiebreakers: PTS -> GD -> GF -> head-to-head GD between tied teams -> rng."""
    # First sort by PTS, GD, GF
    df = df.sort_values(["PTS", "GD", "GF"], ascending=[False, False, False]).reset_index(drop=True)

    # Find groups of teams tied on (PTS, GD, GF) and break by H2H GD
    out_rows: list[dict] = []
    i = 0
    while i < len(df):
        j = i + 1
        while (
            j < len(df)
            and df.iloc[j]["PTS"] == df.iloc[i]["PTS"]
            and df.iloc[j]["GD"] == df.iloc[i]["GD"]
            and df.iloc[j]["GF"] == df.iloc[i]["GF"]
        ):
            j += 1
        block = df.iloc[i:j]
        if len(block) > 1:
            tied_teams = block["team"].tolist()
            h2h_gd = {t: 0 for t in tied_teams}
            for h, a, hg, ag in h2h_results:
                if h in h2h_gd and a in h2h_gd:
                    h2h_gd[h] += hg - ag
                    h2h_gd[a] += ag - hg
            block = block.copy()
            block["_h2h"] = block["team"].map(h2h_gd)
            block["_rng"] = rng.random(len(block))
            block = block.sort_values(["_h2h", "_rng"], ascending=[False, False]).drop(
                columns=["_h2h", "_rng"]
            )
        out_rows.extend(block.to_dict("records"))
        i = j
    return pd.DataFrame(out_rows).reset_index(drop=True)


def _assign_thirds_to_slots(
    slots: list[tuple[int, str]],
    qualifying_groups: set[str],
    rng: np.random.Generator,
) -> dict[int, str]:
    """Assign qualifying third-placed groups to R32 slots respecting candidate lists.

    APPROXIMATION: FIFA's real lookup table is deterministic given which 8 of 12 groups
    have qualifying thirds. Until it's loaded, we attempt a random matching that respects
    each slot's candidate group list. Falls back to greedy if random fails.
    """
    candidate_lists = {
        slot_idx: [g for g in pos.split("/") if g in qualifying_groups] for slot_idx, pos in slots
    }
    # Random matching: shuffle slot order, pick uniformly
    for _ in range(50):
        order = list(slots)
        rng.shuffle(order)
        assignment: dict[int, str] = {}
        used: set[str] = set()
        ok = True
        for slot_idx, _pos in order:
            cands = [g for g in candidate_lists[slot_idx] if g not in used]
            if not cands:
                ok = False
                break
            choice = cands[int(rng.integers(0, len(cands)))]
            assignment[slot_idx] = choice
            used.add(choice)
        if ok and len(assignment) == len(slots):
            return assignment
    # Greedy fallback: assign slots with fewest candidates first
    remaining = list(qualifying_groups)
    rng.shuffle(remaining)
    sorted_slots = sorted(
        slots, key=lambda s: len([g for g in candidate_lists[s[0]] if g in remaining])
    )
    assignment = {}
    for slot_idx, _pos in sorted_slots:
        cands = [g for g in candidate_lists[slot_idx] if g in remaining]
        if not cands:
            # last-resort: take any remaining qualifier
            if remaining:
                choice = remaining[0]
            else:
                continue
        else:
            choice = cands[0]
        assignment[slot_idx] = choice
        if choice in remaining:
            remaining.remove(choice)
    return assignment


def _resolve_pos(
    pos: str,
    position_map: dict[str, str],
    winners: dict[int, str],
    losers: dict[int, str],
    slot_assignment: dict[int, str],
    current_slot_idx: int,
    third_team_by_group: dict[str, str],
) -> str | None:
    if pos in position_map:
        return position_map[pos]
    if pos.startswith("W"):
        return winners.get(int(pos[1:]))
    if pos.startswith("L"):
        return losers.get(int(pos[1:]))
    if "/" in pos:
        # third-place placeholder; look up via slot_assignment
        g = slot_assignment.get(current_slot_idx)
        if g is None:
            return None
        return third_team_by_group.get(g)
    if len(pos) == 2 and pos[0] == "3":
        return third_team_by_group.get(pos[1])
    return None


# ----------------------------------------------------------------------
# Predictor factories
# ----------------------------------------------------------------------


def _build_dixon_coles_predictor(asof: str) -> tuple[PredictFn, StrengthFn]:
    from src.models.dixon_coles import fit, predict

    matches = pd.read_parquet("data/processed/matches.parquet")
    model = fit(matches[["date", "home_team", "away_team", "home_goals", "away_goals"]], asof)

    # Neutral fallback for teams not in training data (uniform low-scoring Poisson approx)
    fallback_dim = 9
    _x = np.arange(fallback_dim)
    import math

    _p = np.exp(-1.3) * (1.3**_x) / np.array([math.factorial(i) for i in _x])
    _p /= _p.sum()
    fallback = np.outer(_p, _p)
    known_teams = set(getattr(model, "teams", []))
    if not known_teams:
        # introspect from params
        for k in getattr(model, "params", {}):
            if k.startswith("attack_"):
                known_teams.add(k[len("attack_") :])

    def predict_fn(home: str, away: str) -> np.ndarray:
        if home not in known_teams or away not in known_teams:
            return fallback
        try:
            return predict(model, home, away, max_goals=8).score_matrix
        except Exception:
            return fallback

    # Use Dixon-Coles attack/defence params as a strength proxy
    def strength_fn(team: str) -> float:
        try:
            params = model.params
            atk = params.get(f"attack_{team}", 0.0)
            dfn = params.get(f"defense_{team}", 0.0)
            return float(atk - dfn) * 10.0  # scale so 0.02 coefficient stays sane
        except Exception:
            return 0.0

    return predict_fn, strength_fn


def _build_uniform_predictor(max_goals: int = 5) -> PredictFn:
    """Dummy predictor: uniform over scorelines up to max_goals each."""
    dim = max_goals + 1
    sm = np.ones((dim, dim), dtype=np.float64) / (dim * dim)

    def predict_fn(_home: str, _away: str) -> np.ndarray:
        return sm

    return predict_fn


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="WC 2026 Monte Carlo simulator")
    parser.add_argument("--n", type=int, default=50000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--predictor", choices=["dixon_coles", "uniform"], default="dixon_coles")
    parser.add_argument("--asof", type=str, default="2026-05-18")
    parser.add_argument("--no-save", action="store_true")
    args = parser.parse_args()

    if args.predictor == "dixon_coles":
        predict_fn, strength_fn = _build_dixon_coles_predictor(args.asof)
        sim = TournamentSim(predict_fn, strength_fn=strength_fn)
    else:
        sim = TournamentSim(_build_uniform_predictor())

    print(f"Running {args.n} sims with predictor={args.predictor} asof={args.asof}")
    res = sim.run(n_sims=args.n, seed=args.seed, save=not args.no_save)
    print(f"Elapsed: {res.seconds:.1f}s ({res.n_sims / max(res.seconds, 1e-9):.1f} sims/s)")
    if res.out_dir:
        print(f"Wrote: {res.out_dir}")
    print("\nTop 5 champion probabilities:")
    print(res.advancement[["team", "p_champion"]].head(5).to_string(index=False))


if __name__ == "__main__":
    main()
