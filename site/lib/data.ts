// Build-time JSON data loaders. All JSON lives in /public/data/*.json and is read
// from disk at build via fs (server components only) so the bundles stay lean.
import fs from "node:fs";
import path from "node:path";

const DATA_DIR = path.join(process.cwd(), "public", "data");

function readJson<T>(name: string): T {
  return JSON.parse(fs.readFileSync(path.join(DATA_DIR, name), "utf-8")) as T;
}

export type Team = {
  team: string;
  iso2: string;
  fifa_code: string;
  conf: string;
  nickname: string;
  fifa_rank: number;
  best_wc: string;
  flag_url: string;
  group: string;
  p_champion: number;
  p_advance_group: number;
};

export type Fixture = {
  num: number;
  date: string;
  venue: string;
  stage: string;
  group: string | null;
  home: string;
  away: string;
  home_pos: string | null;
  away_pos: string | null;
  stadium: string;
  city: string;
  country: string;
  lat: number;
  lon: number;
  altitude_m: number;
  indoor: boolean;
  roof: string;
};

export type Venue = {
  key: string;
  stadium: string;
  city: string;
  country: string;
  lat: number;
  lon: number;
  altitude_m: number;
  capacity: number;
  indoor: boolean;
  roof: string;
};

export type Advancement = {
  team: string;
  p_advance_group: number;
  p_R32_win: number;
  p_R16_win: number;
  p_QF_win: number;
  p_SF_win: number;
  p_final_win: number;
  p_champion: number;
  p_third_place: number;
};

export type MatchProb = {
  num: number;
  home: string;
  away: string;
  n_played: number;
  p_home_win: number;
  p_draw: number;
  p_away_win: number;
  expected_home_goals: number;
  expected_away_goals: number;
};

export type GroupRow = { group: string; team: string };

export type RoundOcc = { stage: string; team: string; n: number; pct: number };

export type BacktestRow = {
  date: string;
  home_team: string;
  away_team: string;
  home_goals: number;
  away_goals: number;
  p_home: number;
  p_draw: number;
  p_away: number;
  outcome: number;
};

export type Meta = {
  sim_run: string;
  n_sims: number;
  n_matches: number;
  n_teams: number;
  kickoff_iso: string;
  generated_at: string;
};

let _cache: Record<string, unknown> = {};
function cached<T>(key: string, loader: () => T): T {
  if (!_cache[key]) _cache[key] = loader();
  return _cache[key] as T;
}

export const getTeams = () => cached("teams", () => readJson<Team[]>("teams.json"));
export const getFixtures = () => cached("fixtures", () => readJson<Fixture[]>("fixtures.json"));
export const getVenues = () => cached("venues", () => readJson<Venue[]>("venues.json"));
export const getAdvancement = () => cached("adv", () => readJson<Advancement[]>("advancement.json"));
export const getMatchProbs = () => cached("mp", () => readJson<MatchProb[]>("match_probs.json"));
export const getGroups = () => cached("grp", () => readJson<GroupRow[]>("groups.json"));
export const getRoundOccupancy = () => cached("occ", () => readJson<RoundOcc[]>("round_occupancy.json"));
export const getMeta = () => cached("meta", () => readJson<Meta>("meta.json"));
export const getBacktestWC = () => cached("btw", () => readJson<BacktestRow[]>("backtest_wc2022.json"));
export const getBacktestEU = () => cached("bte", () => readJson<BacktestRow[]>("backtest_euro2024.json"));

export function getTeamByCode(code: string): Team | undefined {
  return getTeams().find((t) => t.fifa_code.toLowerCase() === code.toLowerCase());
}

export function teamsByGroup(): Record<string, Team[]> {
  const out: Record<string, Team[]> = {};
  for (const t of getTeams()) {
    if (!t.group) continue;
    (out[t.group] ||= []).push(t);
  }
  Object.values(out).forEach((arr) => arr.sort((a, b) => b.p_champion - a.p_champion));
  return out;
}

export function fmtPct(p: number, digits = 1): string {
  if (p == null || isNaN(p)) return "—";
  if (p < 0.001) return "<0.1%";
  return `${(p * 100).toFixed(digits)}%`;
}

// Ranked Probability Score for a 3-way classifier with ordinal outcome (0=home,1=draw,2=away)
export function rps(p: [number, number, number], outcome: number): number {
  const o = [0, 0, 0];
  o[outcome] = 1;
  let c1 = 0, c2 = 0, s = 0;
  for (let i = 0; i < 2; i++) {
    c1 += p[i];
    c2 += o[i];
    s += (c1 - c2) ** 2;
  }
  return s / 2;
}

export function averageRPS(rows: BacktestRow[]): number {
  if (!rows.length) return 0;
  return (
    rows.reduce(
      (acc, r) => acc + rps([r.p_home, r.p_draw, r.p_away], r.outcome),
      0,
    ) / rows.length
  );
}

export function logLoss(rows: BacktestRow[]): number {
  if (!rows.length) return 0;
  const probs = ["p_home", "p_draw", "p_away"] as const;
  let s = 0;
  for (const r of rows) {
    const p = Math.max(1e-9, r[probs[r.outcome]] ?? 1e-9);
    s -= Math.log(p);
  }
  return s / rows.length;
}
