"""Produce the final quiniela deliverable from a Monte Carlo sim run.

End of the pipeline: sim run (advancement + match_probs parquets) → pool-EV-optimal
picks under a rubric → tracked artifacts in `data/picks/<sim_run>/`:

  * `quiniela.json` — machine-readable: meta (sim run, caveats, freshness), the N pool
    entries with per-match picks + EV, and the knockout bracket picks.
  * `entries.csv`   — long format, one row per (entry, match).
  * `quiniela.md`   — the human-readable quiniela card.

Group-stage picks come from `optimize_entries` (chalk / moderate / high-variance);
knockout picks from `pick_bracket` (chalk + a contrarian variant). Score matrices for
totals / exact-score EV are reconstructed from the sim's trusted 1X2 via the DC-tau
joint (`src.models.dc_joint`) — the persisted expected-goal columns are NOT used
because pre-canonicalization sim runs polluted them (uniform-fallback artifacts).

Usage:
    uv run python -m src.strategy.make_quiniela                      # latest sim run
    uv run python -m src.strategy.make_quiniela --sim-run data/sims/sim_run_202605211148 \
        --rubric configs/rubrics/fifa_quiniela_mx.yaml --n-entries 3
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from src.models.dc_joint import DEFAULT_RHO, score_matrix_from_1x2
from src.sims.bracket_2026 import GROUP_MATCHES
from src.strategy.bracket_picks import BracketPick, pick_bracket
from src.strategy.optimize_entries import Entry, optimize_entries
from src.strategy.pool_ev import Rubric, load_rubric
from src.strategy.public_estimator import estimate_public_champion, estimate_public_picks

RUBRICS_DIR = Path("configs/rubrics")
MARKET_PATH = Path("data/processed/market_odds_wc2026.parquet")


def latest_sim_run(root: str | Path = "data/sims") -> Path:
    runs = sorted(Path(root).glob("sim_run_*"))
    if not runs:
        raise FileNotFoundError(f"no sim_run_* directories under {root}")
    return runs[-1]


def build_entry_inputs(
    match_probs: pd.DataFrame,
    rho: float = DEFAULT_RHO,
    max_goals: int = 10,
) -> pd.DataFrame:
    """Adapt sim match_probs (group stage only) to the optimizer contract.

    Renames num/home/away → match_num/home_team/away_team and attaches a DC-tau
    score matrix per match implied by the sim's 1X2.
    """
    df = match_probs[match_probs["home"].notna() & match_probs["away"].notna()].copy()
    df = df.rename(columns={"num": "match_num", "home": "home_team", "away": "away_team"})
    df = df.sort_values("match_num").reset_index(drop=True)
    df["score_matrix"] = [
        score_matrix_from_1x2(
            r["p_home_win"], r["p_draw"], r["p_away_win"], rho=rho, max_goals=max_goals
        )
        for _, r in df.iterrows()
    ]
    return df


def load_market_probs() -> pd.DataFrame | None:
    """De-vigged market 1X2 keyed to match numbers, if the snapshot exists."""
    if not MARKET_PATH.exists():
        return None
    mdf = pd.read_parquet(MARKET_PATH)
    num_by_pair = {(m["home"], m["away"]): m["num"] for m in GROUP_MATCHES}
    mdf["match_num"] = [
        num_by_pair.get((r["home_team"], r["away_team"])) for _, r in mdf.iterrows()
    ]
    mdf = mdf.dropna(subset=["match_num"])
    return mdf.rename(
        columns={
            "p_home_market": "p_home_win",
            "p_draw_market": "p_draw",
            "p_away_market": "p_away_win",
        }
    )[["match_num", "p_home_win", "p_draw", "p_away_win"]]


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------


def _pick_to_dict(pick: object, rubric_type: str) -> dict:
    if rubric_type == "composite_1x2_totals":
        result, totals = pick  # type: ignore[misc]
        return {"result": result, "totals": totals}
    if rubric_type == "exact_score_tiered":
        h, a = pick  # type: ignore[misc]
        return {"home_goals": int(h), "away_goals": int(a)}
    return {"result": str(pick)}


def _pick_to_str(pick: object, rubric_type: str) -> str:
    d = _pick_to_dict(pick, rubric_type)
    if rubric_type == "composite_1x2_totals":
        return f"{d['result']} {'O2.5' if d['totals'] == 'OVER' else 'U2.5'}"
    if rubric_type == "exact_score_tiered":
        return f"{d['home_goals']}-{d['away_goals']}"
    return d["result"]


def _entry_to_dict(entry: Entry, rubric_type: str) -> dict:
    picks = [
        {
            "match_num": int(r["match_num"]),
            "home_team": r["home_team"],
            "away_team": r["away_team"],
            **_pick_to_dict(r["pick"], rubric_type),
            "ev": round(float(r["ev"]), 4),
        }
        for _, r in entry.picks.iterrows()
    ]
    return {
        "label": entry.label,
        "expected_points": round(float(entry.expected_points), 2),
        "expected_pool_rank_pct": round(float(entry.expected_pool_rank_pct), 3),
        "reasoning": entry.reasoning,
        "diagnostics": {k: float(v) for k, v in entry.diagnostics.items()},
        "picks": picks,
    }


def _bracket_to_dict(bp: BracketPick) -> dict:
    return {
        "picks_by_round": bp.picks_by_round,
        "expected_points": round(float(bp.expected_points), 1),
        "reasoning": bp.reasoning,
    }


def _entries_long_csv(entries: list[Entry], rubric_type: str) -> pd.DataFrame:
    rows = []
    for e in entries:
        for _, r in e.picks.iterrows():
            rows.append(
                {
                    "entry": e.label,
                    "match_num": int(r["match_num"]),
                    "home_team": r["home_team"],
                    "away_team": r["away_team"],
                    "pick": _pick_to_str(r["pick"], rubric_type),
                    "ev": round(float(r["ev"]), 4),
                }
            )
    return pd.DataFrame(rows)


def _render_markdown(
    entries: list[Entry],
    brackets: dict[str, BracketPick],
    rubric: Rubric,
    meta: dict,
) -> str:
    by_num = {m["num"]: m for m in GROUP_MATCHES}
    lines = [
        "# WC2026 Quiniela — final picks",
        "",
        f"Generated {meta['generated_at']} from `{meta['sim_run']}` "
        f"({meta['n_sims']:,} Monte Carlo sims). Rubric: **{rubric.name}**.",
        "",
    ]
    if meta["caveats"]:
        lines.append("**Caveats (read before trusting):**")
        lines += [f"- {c}" for c in meta["caveats"]]
        lines.append("")

    lines.append("## Group stage — entry portfolio")
    lines.append("")
    header = (
        f"| # | Grp | Fixture | {' | '.join(e.label for e in entries)} |"
        f"\n|---|-----|---------|{'|'.join(['---'] * len(entries))}|"
    )
    lines.append(header)
    first = entries[0].picks
    pick_strs = [[_pick_to_str(p, rubric.type) for p in e.picks["pick"]] for e in entries]
    for k, (_, r) in enumerate(first.iterrows()):
        num = int(r["match_num"])
        grp = by_num.get(num, {}).get("group", "")
        cells = " | ".join(ps[k] for ps in pick_strs)
        lines.append(f"| {num} | {grp} | {r['home_team']} vs {r['away_team']} | {cells} |")
    lines.append("")
    for e in entries:
        lines.append(
            f"- **{e.label}** — E[points] = {e.expected_points:.1f}, "
            f"public overlap = {e.diagnostics.get('total_overlap', float('nan')):.1f}"
        )
    lines.append("")

    lines.append("## Knockout bracket (ESPN-style points)")
    lines.append("")
    for label, bp in brackets.items():
        lines.append(f"### {label} — E[points] = {bp.expected_points:.0f}")
        for rname in ("R32", "R16", "QF", "SF", "F", "W"):
            teams = bp.picks_by_round.get(rname)
            if teams:
                lines.append(f"- **{rname}**: {', '.join(teams)}")
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def make_quiniela(
    sim_run: Path,
    rubric_path: Path,
    bracket_rubric_path: Path,
    out_root: Path,
    n_entries: int = 3,
    square_money_weight: float = 0.5,
    contrarian_weight: float = 0.3,
    rho: float = DEFAULT_RHO,
) -> Path:
    advancement = pd.read_parquet(sim_run / "advancement.parquet")
    match_probs = pd.read_parquet(sim_run / "match_probs.parquet")
    n_sims = int(match_probs["n_played"].max()) if "n_played" in match_probs.columns else 0

    rubric = load_rubric(rubric_path)
    bracket_rubric = load_rubric(bracket_rubric_path)

    entry_inputs = build_entry_inputs(match_probs, rho=rho)
    market = load_market_probs()
    if market is not None:
        # Partial market coverage must not drop matches: fall back to model probs.
        base = entry_inputs[["match_num", "p_home_win", "p_draw", "p_away_win"]]
        merged = base.merge(market, on="match_num", how="left", suffixes=("_model", ""))
        for c in ("p_home_win", "p_draw", "p_away_win"):
            merged[c] = merged[c].fillna(merged[f"{c}_model"])
        market = merged[["match_num", "p_home_win", "p_draw", "p_away_win"]]
    public = estimate_public_picks(
        entry_inputs, market_probs=market, square_money_weight=square_money_weight
    )
    entries = optimize_entries(entry_inputs, public, rubric, n_entries=n_entries)

    public_champ = estimate_public_champion(advancement, square_money_weight=square_money_weight)
    brackets = {
        "chalk": pick_bracket(advancement, bracket_rubric),
        "contrarian": pick_bracket(
            advancement,
            bracket_rubric,
            public_picks=public_champ,
            contrarian_weight=contrarian_weight,
        ),
    }

    caveats = [
        f"Model freshness: predictions come from `{sim_run.name}`; the sim was generated "
        "from training data as of its run date — re-run `src.predict_wc2026` after a data "
        "refresh for kickoff-fresh numbers.",
        "Score matrices for totals/exact-score EV are DC-tau joints implied by the blended "
        f"1X2 (rho={rho}); the sim's expected-goal columns are not used.",
    ]
    if market is None:
        caveats.append(
            "No de-vigged market snapshot on disk (`data/processed/market_odds_wc2026.parquet`); "
            "picks are model-only and the public estimate uses the model as its sharp prior."
        )
    else:
        caveats.append("Public-pick estimate anchored to the de-vigged market snapshot.")

    meta = {
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"),
        "sim_run": sim_run.name,
        "n_sims": n_sims,
        "rubric": rubric.name,
        "bracket_rubric": bracket_rubric.name,
        "market_anchored": market is not None,
        "square_money_weight": square_money_weight,
        "contrarian_weight": contrarian_weight,
        "rho": rho,
        "caveats": caveats,
    }

    out_dir = out_root / sim_run.name
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        **meta,
        "entries": [_entry_to_dict(e, rubric.type) for e in entries],
        "bracket": {k: _bracket_to_dict(v) for k, v in brackets.items()},
    }
    (out_dir / "quiniela.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    _entries_long_csv(entries, rubric.type).to_csv(out_dir / "entries.csv", index=False)
    (out_dir / "quiniela.md").write_text(_render_markdown(entries, brackets, rubric, meta))
    return out_dir


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sim-run", default=None, help="sim run dir (default: latest under data/sims)")
    p.add_argument("--rubric", default=str(RUBRICS_DIR / "fifa_quiniela_mx.yaml"))
    p.add_argument("--bracket-rubric", default=str(RUBRICS_DIR / "espn_bracket.yaml"))
    p.add_argument("--n-entries", type=int, default=3)
    p.add_argument("--square-money-weight", type=float, default=0.5)
    p.add_argument("--contrarian-weight", type=float, default=0.3)
    p.add_argument("--rho", type=float, default=DEFAULT_RHO)
    p.add_argument("--out", default="data/picks")
    args = p.parse_args(argv)

    sim_run = Path(args.sim_run) if args.sim_run else latest_sim_run()
    print(f"Sim run: {sim_run}")
    out_dir = make_quiniela(
        sim_run=sim_run,
        rubric_path=Path(args.rubric),
        bracket_rubric_path=Path(args.bracket_rubric),
        out_root=Path(args.out),
        n_entries=args.n_entries,
        square_money_weight=args.square_money_weight,
        contrarian_weight=args.contrarian_weight,
        rho=args.rho,
    )
    payload = json.loads((out_dir / "quiniela.json").read_text())
    print(f"Wrote {out_dir}/quiniela.json, entries.csv, quiniela.md")
    for e in payload["entries"]:
        print(f"  entry {e['label']:20s} E[points]={e['expected_points']:.1f}")
    for k, b in payload["bracket"].items():
        champ = b["picks_by_round"].get("W", ["?"])[0]
        print(f"  bracket {k:18s} E[points]={b['expected_points']:.0f}  champion={champ}")
    if not payload["market_anchored"]:
        print("  NOTE: model-only (no market snapshot on disk) — see caveats in quiniela.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
