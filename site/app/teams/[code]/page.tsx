import { notFound } from "next/navigation";
import Link from "next/link";
import FlagImg from "@/components/FlagImg";
import ConfederationChip from "@/components/ConfederationChip";
import ProbabilityBar from "@/components/ProbabilityBar";
import L from "@/components/L";
import {
  getTeams,
  getTeamByCode,
  getAdvancement,
  getFixtures,
  getMatchProbs,
  getMeta,
  fmtPct,
} from "@/lib/data";
import { fmtDate } from "@/lib/utils";

export function generateStaticParams() {
  return getTeams().map((t) => ({ code: t.fifa_code.toLowerCase() }));
}

export async function generateMetadata({ params }: { params: Promise<{ code: string }> }) {
  const { code } = await params;
  const t = getTeamByCode(code);
  return { title: t ? `${t.team} — predictions` : "Team" };
}

export default async function TeamPage({ params }: { params: Promise<{ code: string }> }) {
  const { code } = await params;
  const team = getTeamByCode(code);
  if (!team) notFound();

  const adv = getAdvancement().find((a) => a.team === team.team);
  const allTeams = getTeams();
  const fixtures = getFixtures();
  const probs = getMatchProbs();
  const teamMap = new Map(allTeams.map((t) => [t.team, t]));
  const probMap = new Map(probs.map((p) => [p.num, p]));

  const groupFixtures = fixtures.filter(
    (f) => f.stage === "group" && (f.home === team.team || f.away === team.team),
  );

  const groupTeams = allTeams.filter((t) => t.group === team.group && t.team !== team.team);

  const rounds = adv
    ? [
        { label: "Advance Group", value: adv.p_advance_group },
        { label: "Round of 32", value: adv.p_R32_win },
        { label: "Round of 16", value: adv.p_R16_win },
        { label: "Quarterfinal", value: adv.p_QF_win },
        { label: "Semifinal", value: adv.p_SF_win },
        { label: "Final", value: adv.p_final_win },
        { label: "Champion", value: adv.p_champion },
      ]
    : [];

  return (
    <div>
      {/* Hero */}
      <section className="relative overflow-hidden border-b-2 border-[color:var(--color-ink)]">
        <div className="mx-auto max-w-7xl px-6 py-12 flex flex-col md:flex-row md:items-end gap-8">
          <FlagImg iso2={team.iso2} size={180} priority />
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <ConfederationChip conf={team.conf} />
              <span className="text-xs text-[color:var(--color-ink-soft)]"><L es="Grupo" en="Group" /> {team.group}</span>
              <span className="text-xs text-[color:var(--color-ink-soft)]">·</span>
              <span className="text-xs text-[color:var(--color-ink-soft)]">FIFA #{team.fifa_rank}</span>
            </div>
            <h1 className="display text-5xl sm:text-7xl text-[color:var(--color-ink)]">{team.team}</h1>
            <p className="text-[color:var(--color-ink-soft)] italic mt-2 text-lg">{team.nickname}</p>
            <p className="text-[color:var(--color-ink-soft)] text-sm mt-1"><L es="Mejor actuación en Mundiales:" en="Best WC finish:" /> {team.best_wc}</p>
          </div>
          <div className="md:text-right">
            <div className="text-xs uppercase tracking-wider text-[color:var(--color-ink-soft)]">P(Champion)</div>
            <div className="display text-5xl text-[color:var(--color-red)]">{fmtPct(team.p_champion ?? 0, 1)}</div>
            <div className="text-xs text-[color:var(--color-ink-soft)] mt-1"><L es="en" en="across" /> {getMeta().n_sims.toLocaleString()} <L es="simulaciones" en="sims" /></div>
          </div>
        </div>
      </section>

      {/* Advancement waterfall */}
      <section className="mx-auto max-w-7xl px-6 py-12">
        <h2 className="display text-2xl mb-6 text-[color:var(--color-ink)]"><L es="Cascada de avance" en="Advancement waterfall" /></h2>
        <div className="space-y-3 max-w-3xl">
          {rounds.map((r, i) => (
            <ProbabilityBar
              key={r.label}
              value={r.value}
              label={r.label}
              rightLabel={fmtPct(r.value)}
              color={i === rounds.length - 1 ? "amber" : "emerald"}
              delay={i * 0.05}
              height={10}
            />
          ))}
        </div>
      </section>

      {/* Group fixtures */}
      <section className="mx-auto max-w-7xl px-6 py-6">
        <h2 className="display text-2xl mb-4 text-[color:var(--color-ink)]"><L es="Partidos de fase de grupos" en="Group stage fixtures" /></h2>
        <div className="grid sm:grid-cols-3 gap-4">
          {groupFixtures.map((f) => {
            const p = probMap.get(f.num);
            const isHome = f.home === team.team;
            const opp = isHome ? f.away : f.home;
            const oppTeam = teamMap.get(opp);
            const pWin = isHome ? p?.p_home_win ?? 0 : p?.p_away_win ?? 0;
            const pDraw = p?.p_draw ?? 0;
            const pLose = isHome ? p?.p_away_win ?? 0 : p?.p_home_win ?? 0;
            const xg = isHome ? p?.expected_home_goals ?? 0 : p?.expected_away_goals ?? 0;
            const xgOpp = isHome ? p?.expected_away_goals ?? 0 : p?.expected_home_goals ?? 0;
            return (
              <Link
                key={f.num}
                href={`/matches/${f.num}`}
                className="sticker sticker-hover p-4 block"
              >
                <div className="text-[11px] text-[color:var(--color-ink-soft)]">{fmtDate(f.date)} · {isHome ? "vs" : "@"}</div>
                <div className="flex items-center gap-2 mt-2">
                  {oppTeam && <FlagImg iso2={oppTeam.iso2} size={32} />}
                  <span className="display text-sm leading-none text-[color:var(--color-ink)]">{opp}</span>
                </div>
                <div data-l="en" className="mt-3 text-xs text-[color:var(--color-ink-soft)]">
                  Expected score <span className="text-[color:var(--color-ink)] tabular-nums">{xg.toFixed(1)} – {xgOpp.toFixed(1)}</span>
                </div>
                <div data-l="es" className="mt-3 text-xs text-[color:var(--color-ink-soft)]">
                  Marcador esperado <span className="text-[color:var(--color-ink)] tabular-nums">{xg.toFixed(1)} – {xgOpp.toFixed(1)}</span>
                </div>
                <div className="mt-3 grid grid-cols-3 gap-1 text-[11px] text-center">
                  <div className="border-2 border-[color:var(--color-ink)] bg-[color:var(--color-green)] py-1">
                    <div className="display text-sm leading-none text-[color:var(--color-card)]">{fmtPct(pWin)}</div>
                    <div className="text-[color:var(--color-card)]"><L es="Gana" en="Win" /></div>
                  </div>
                  <div className="border-2 border-[color:var(--color-ink)] bg-[color:var(--color-yellow)] py-1">
                    <div className="display text-sm leading-none text-[color:var(--color-ink)]">{fmtPct(pDraw)}</div>
                    <div className="text-[color:var(--color-ink-soft)]"><L es="Empata" en="Draw" /></div>
                  </div>
                  <div className="border-2 border-[color:var(--color-ink)] bg-[color:var(--color-red)] py-1">
                    <div className="display text-sm leading-none text-[color:var(--color-card)]">{fmtPct(pLose)}</div>
                    <div className="text-[color:var(--color-card)]"><L es="Pierde" en="Lose" /></div>
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      </section>

      {/* Group rivals */}
      <section className="mx-auto max-w-7xl px-6 py-12">
        <h2 data-l="en" className="display text-2xl mb-4 text-[color:var(--color-ink)]">Group {team.group} rivals</h2>
        <h2 data-l="es" className="display text-2xl mb-4 text-[color:var(--color-ink)]">Rivales del Grupo {team.group}</h2>
        <div className="grid sm:grid-cols-3 gap-3">
          {groupTeams.map((t) => (
            <Link key={t.fifa_code} href={`/teams/${t.fifa_code.toLowerCase()}`} className="sticker sticker-hover p-3 flex items-center gap-3">
              <FlagImg iso2={t.iso2} size={36} />
              <div className="flex-1 min-w-0">
                <div className="display text-sm leading-none truncate text-[color:var(--color-ink)]">{t.team}</div>
                <div className="text-xs text-[color:var(--color-ink-soft)] mt-1">FIFA #{t.fifa_rank}</div>
              </div>
              <div className="text-right">
                <div className="text-[10px] text-[color:var(--color-ink-soft)]">Advance</div>
                <div className="display text-sm leading-none text-[color:var(--color-blue)]">{fmtPct(t.p_advance_group ?? 0)}</div>
              </div>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}
