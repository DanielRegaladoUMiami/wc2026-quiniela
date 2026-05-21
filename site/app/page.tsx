import Link from "next/link";
import Hero from "@/components/Hero";
import FlagImg from "@/components/FlagImg";
import ProbabilityBar from "@/components/ProbabilityBar";
import {
  getAdvancement,
  getTeams,
  getFixtures,
  getMatchProbs,
  fmtPct,
} from "@/lib/data";
import { fmtDate } from "@/lib/utils";

export default function Page() {
  const adv = getAdvancement();
  const teams = getTeams();
  const fixtures = getFixtures();
  const probs = getMatchProbs();

  const teamMap = new Map(teams.map((t) => [t.team, t]));
  const top = [...adv].sort((a, b) => b.p_champion - a.p_champion).slice(0, 8);

  const today = Date.now();
  const upcoming = fixtures
    .filter((f) => new Date(f.date).getTime() >= today - 12 * 3600 * 1000)
    .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
    .slice(0, 6);
  const probMap = new Map(probs.map((p) => [p.num, p]));

  return (
    <div>
      <Hero />

      <section className="mx-auto max-w-7xl px-6 py-16">
        <div className="flex items-end justify-between mb-8">
          <div>
            <h2 className="font-display text-3xl sm:text-4xl font-bold tracking-tight">
              Champion probabilities
            </h2>
            <p className="text-slate-400 mt-1">Top 8 nations by P(win the World Cup).</p>
          </div>
          <Link href="/teams" className="text-sm text-emerald-400 hover:text-emerald-300 hidden sm:inline">
            All 48 teams →
          </Link>
        </div>
        <div className="grid sm:grid-cols-2 gap-x-10 gap-y-4">
          {top.map((row, i) => {
            const t = teamMap.get(row.team);
            return (
              <Link
                key={row.team}
                href={t ? `/teams/${t.fifa_code.toLowerCase()}` : "#"}
                className="group flex items-center gap-3 py-2 rounded-lg hover:bg-white/[0.025] px-2 -mx-2 transition-colors"
              >
                <div className="w-5 text-xs text-slate-600 tabular-nums">{i + 1}</div>
                {t && <FlagImg iso2={t.iso2} size={36} />}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium truncate">{row.team}</span>
                    <span className="font-display tabular-nums text-emerald-300 font-semibold">
                      {fmtPct(row.p_champion)}
                    </span>
                  </div>
                  <ProbabilityBar value={row.p_champion} max={top[0].p_champion} delay={i * 0.04} height={6} />
                </div>
              </Link>
            );
          })}
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-6 py-12 border-t border-[color:var(--color-line)]">
        <div className="flex items-end justify-between mb-8">
          <div>
            <h2 className="font-display text-3xl sm:text-4xl font-bold tracking-tight">Opening fixtures</h2>
            <p className="text-slate-400 mt-1">First six matches of the tournament.</p>
          </div>
          <Link href="/matches" className="text-sm text-emerald-400 hover:text-emerald-300">
            All 104 matches →
          </Link>
        </div>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {upcoming.map((f) => {
            const home = teamMap.get(f.home);
            const away = teamMap.get(f.away);
            const p = probMap.get(f.num);
            return (
              <Link
                key={f.num}
                href={`/matches/${f.num}`}
                className="glass rounded-xl p-4 hover:border-emerald-500/30 transition-colors block"
              >
                <div className="flex items-center justify-between text-[11px] text-slate-500 mb-3">
                  <span>{fmtDate(f.date)} · {f.stage}{f.group ? ` ${f.group}` : ""}</span>
                  <span className="text-slate-600">M{f.num}</span>
                </div>
                <div className="space-y-2">
                  <div className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-2 min-w-0">
                      {home && <FlagImg iso2={home.iso2} size={28} />}
                      <span className="truncate text-sm font-medium">{f.home}</span>
                    </div>
                    <span className="text-xs tabular-nums text-emerald-300">{fmtPct(p?.p_home_win ?? 0)}</span>
                  </div>
                  <div className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-2 min-w-0">
                      {away && <FlagImg iso2={away.iso2} size={28} />}
                      <span className="truncate text-sm font-medium">{f.away}</span>
                    </div>
                    <span className="text-xs tabular-nums text-amber-300">{fmtPct(p?.p_away_win ?? 0)}</span>
                  </div>
                </div>
                <div className="mt-3 pt-3 border-t border-[color:var(--color-line)] text-[11px] text-slate-500 flex items-center justify-between">
                  <span>{f.stadium}, {f.city}</span>
                  {f.altitude_m > 1000 && <span className="text-amber-400">+{f.altitude_m}m</span>}
                </div>
              </Link>
            );
          })}
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-6 py-16">
        <div className="glass rounded-2xl p-8 sm:p-12 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
          <div>
            <h3 className="font-display text-2xl sm:text-3xl font-bold">Build your quiniela.</h3>
            <p className="text-slate-400 mt-2 max-w-md">
              Every probability on this site is reproducible. Clone the repo, run the pipeline, or steal the picks.
            </p>
          </div>
          <div className="flex gap-3">
            <a
              href="https://github.com/DanielRegaladoUMiami/wc2026-quiniela"
              className="rounded-lg bg-white/5 hover:bg-white/10 border border-[color:var(--color-line)] px-5 py-2.5 text-sm font-medium"
            >
              View on GitHub
            </a>
            <Link
              href="/bracket"
              className="rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 px-5 py-2.5 text-sm font-semibold"
            >
              See the bracket
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
