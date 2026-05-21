import { notFound } from "next/navigation";
import Link from "next/link";
import FlagImg from "@/components/FlagImg";
import {
  getFixtures,
  getMatchProbs,
  getTeams,
  fmtPct,
} from "@/lib/data";
import { fmtDate } from "@/lib/utils";
import ScoreHeatmap from "./ScoreHeatmap";
import ProbDonut from "./ProbDonut";

export function generateStaticParams() {
  return getFixtures().map((f) => ({ num: String(f.num) }));
}

export async function generateMetadata({ params }: { params: Promise<{ num: string }> }) {
  const { num } = await params;
  const f = getFixtures().find((x) => x.num === Number(num));
  return { title: f ? `${f.home} vs ${f.away}` : "Match" };
}

export default async function MatchPage({ params }: { params: Promise<{ num: string }> }) {
  const { num } = await params;
  const n = Number(num);
  const fixture = getFixtures().find((f) => f.num === n);
  if (!fixture) notFound();
  const prob = getMatchProbs().find((p) => p.num === n);
  const teamMap = new Map(getTeams().map((t) => [t.team, t]));
  const home = teamMap.get(fixture.home);
  const away = teamMap.get(fixture.away);

  const pH = prob?.p_home_win ?? 0;
  const pD = prob?.p_draw ?? 0;
  const pA = prob?.p_away_win ?? 0;
  const xgH = prob?.expected_home_goals ?? 0;
  const xgA = prob?.expected_away_goals ?? 0;
  const pick = pH > pD && pH > pA ? `${fixture.home} win` : pA > pD ? `${fixture.away} win` : "Draw";

  return (
    <div>
      <section className="relative overflow-hidden border-b border-[color:var(--color-line)]">
        <div className="absolute inset-0 -z-10 opacity-30">
          <div className="absolute top-0 left-0 h-80 w-80 rounded-full bg-emerald-500/30 blur-[120px]" />
          <div className="absolute top-0 right-0 h-80 w-80 rounded-full bg-amber-400/20 blur-[120px]" />
        </div>
        <div className="mx-auto max-w-7xl px-6 py-12">
          <Link href="/matches" className="text-xs text-slate-500 hover:text-white">← All matches</Link>
          <div className="mt-4 text-xs text-slate-400">
            Match {fixture.num} · {fmtDate(fixture.date)} · {fixture.stadium}, {fixture.city}
            {fixture.altitude_m > 1000 && <span className="ml-2 text-amber-400">Altitude +{fixture.altitude_m}m</span>}
          </div>
          <div className="mt-6 grid grid-cols-1 sm:grid-cols-3 gap-6 items-center">
            <div className="flex flex-col sm:items-start items-center text-center sm:text-left gap-3">
              {home && <FlagImg iso2={home.iso2} size={120} priority />}
              <h1 className="font-display text-3xl sm:text-4xl font-bold">{fixture.home}</h1>
              <div className="font-display text-4xl gradient-text">{fmtPct(pH)}</div>
            </div>
            <div className="text-center">
              <div className="text-xs text-slate-500 uppercase tracking-wider">Expected</div>
              <div className="font-display text-5xl font-bold tabular-nums">{xgH.toFixed(1)} <span className="text-slate-700">–</span> {xgA.toFixed(1)}</div>
              <div className="text-xs text-slate-500 mt-2">Draw {fmtPct(pD)}</div>
              <div className="mt-4 inline-block rounded-full bg-emerald-500/10 border border-emerald-500/30 px-3 py-1 text-xs text-emerald-300">
                Pick: {pick}
              </div>
            </div>
            <div className="flex flex-col sm:items-end items-center text-center sm:text-right gap-3">
              {away && <FlagImg iso2={away.iso2} size={120} />}
              <h1 className="font-display text-3xl sm:text-4xl font-bold">{fixture.away}</h1>
              <div className="font-display text-4xl gradient-text">{fmtPct(pA)}</div>
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-6 py-12 grid lg:grid-cols-2 gap-8">
        <div className="glass rounded-xl p-6">
          <h2 className="font-display text-xl font-bold mb-4">1X2 distribution</h2>
          <ProbDonut pH={pH} pD={pD} pA={pA} home={fixture.home} away={fixture.away} />
        </div>
        <div className="glass rounded-xl p-6">
          <h2 className="font-display text-xl font-bold mb-1">Score-line heatmap</h2>
          <p className="text-xs text-slate-500 mb-4">Joint Poisson(λ_home, λ_away) with Dixon-Coles low-score correction.</p>
          <ScoreHeatmap lambdaH={xgH} lambdaA={xgA} />
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-6 pb-16 grid sm:grid-cols-3 gap-4">
        <Card title="Venue">
          <div className="font-medium">{fixture.stadium}</div>
          <div className="text-sm text-slate-400">{fixture.city}, {fixture.country}</div>
          <div className="text-xs text-slate-500 mt-2">Roof: {fixture.roof}{fixture.indoor ? " · indoor" : ""}</div>
        </Card>
        <Card title="Altitude">
          <div className="font-display text-3xl font-bold tabular-nums">{fixture.altitude_m}m</div>
          <div className="text-xs text-slate-500 mt-1">{fixture.altitude_m > 1500 ? "High-altitude penalty applied to non-acclimated teams" : "Sea-level effect negligible"}</div>
        </Card>
        <Card title="How to play this">
          <p className="text-sm text-slate-300">
            {pick.toLowerCase()}. The score most concentrated in the joint distribution is roughly{" "}
            <span className="text-emerald-300 font-medium">{Math.round(xgH)}–{Math.round(xgA)}</span>.
          </p>
          <p className="text-xs text-slate-500 mt-2">Contrarian alternative: the draw at {fmtPct(pD)} if your pool rewards bracket-busters.</p>
        </Card>
      </section>
    </div>
  );
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="glass rounded-xl p-5">
      <div className="text-[10px] uppercase tracking-wider text-slate-500 mb-2">{title}</div>
      {children}
    </div>
  );
}
