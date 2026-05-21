import "server-only";
import fs from "node:fs";
import path from "node:path";
import type {
  Team,
  Fixture,
  Venue,
  Advancement,
  MatchProb,
  GroupRow,
  RoundOcc,
  BacktestRow,
  Meta,
} from "./types";

export * from "./types";

const DATA_DIR = path.join(process.cwd(), "public", "data");

function readJson<T>(name: string): T {
  return JSON.parse(fs.readFileSync(path.join(DATA_DIR, name), "utf-8")) as T;
}

const _cache: Record<string, unknown> = {};
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
