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
import L from "@/components/L";

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
  const pickEn = pH > pD && pH > pA ? `${fixture.home} win` : pA > pD ? `${fixture.away} win` : "Draw";
  const pickEs = pH > pD && pH > pA ? `Gana ${fixture.home}` : pA > pD ? `Gana ${fixture.away}` : "Empate";

  return (
    <div>
      <section className="relative overflow-hidden border-b-2 border-[color:var(--color-ink)]">
        <div className="mx-auto max-w-7xl px-6 py-12">
          <Link href="/matches" className="display text-xs text-[color:var(--color-red)] hover:text-[color:var(--color-ink)]"><L es="← TODOS LOS PARTIDOS" en="← ALL MATCHES" /></Link>
          <div data-l="en" className="mt-4 text-xs text-[color:var(--color-ink-soft)]">
            Match {fixture.num} · {fmtDate(fixture.date)} · {fixture.stadium}, {fixture.city}
            {fixture.altitude_m > 1000 && <span className="ml-2 text-[color:var(--color-red)]">Altitude +{fixture.altitude_m}m</span>}
          </div>
          <div data-l="es" className="mt-4 text-xs text-[color:var(--color-ink-soft)]">
            Partido {fixture.num} · {fmtDate(fixture.date)} · {fixture.stadium}, {fixture.city}
            {fixture.altitude_m > 1000 && <span className="ml-2 text-[color:var(--color-red)]">Altitud +{fixture.altitude_m}m</span>}
          </div>
          <div className="mt-6 grid grid-cols-1 sm:grid-cols-3 gap-6 items-center">
            <div className="flex flex-col sm:items-start items-center text-center sm:text-left gap-3">
              {home && <FlagImg iso2={home.iso2} size={120} priority className="!rounded-none border-2 border-[color:var(--color-ink)] !ring-0" />}
              <h1 className="display text-3xl sm:text-4xl text-[color:var(--color-ink)]">{fixture.home}</h1>
              <div className="display text-4xl text-[color:var(--color-red)]">{fmtPct(pH)}</div>
            </div>
            <div className="text-center">
              <div className="text-xs text-[color:var(--color-ink-soft)] uppercase tracking-wider"><L es="Esperado" en="Expected" /></div>
              <div className="display text-5xl tabular-nums text-[color:var(--color-ink)]">{xgH.toFixed(1)} <span className="text-[color:var(--color-ink-soft)]">–</span> {xgA.toFixed(1)}</div>
              <div className="text-xs text-[color:var(--color-ink-soft)] mt-2"><L es="Empate" en="Draw" /> {fmtPct(pD)}</div>
              <div data-l="en" className="display mt-4 inline-block bg-[color:var(--color-yellow)] border-2 border-[color:var(--color-ink)] px-3 py-1 text-xs text-[color:var(--color-ink)]">
                Pick: {pickEn}
              </div>
              <div data-l="es" className="display mt-4 inline-block bg-[color:var(--color-yellow)] border-2 border-[color:var(--color-ink)] px-3 py-1 text-xs text-[color:var(--color-ink)]">
                Apuesta: {pickEs}
              </div>
            </div>
            <div className="flex flex-col sm:items-end items-center text-center sm:text-right gap-3">
              {away && <FlagImg iso2={away.iso2} size={120} className="!rounded-none border-2 border-[color:var(--color-ink)] !ring-0" />}
              <h1 className="display text-3xl sm:text-4xl text-[color:var(--color-ink)]">{fixture.away}</h1>
              <div className="display text-4xl text-[color:var(--color-red)]">{fmtPct(pA)}</div>
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-6 py-12 grid lg:grid-cols-2 gap-8">
        <div className="sticker p-6">
          <h2 className="display text-xl mb-4 text-[color:var(--color-ink)]"><L es="DISTRIBUCIÓN 1X2" en="1X2 DISTRIBUTION" /></h2>
          <ProbDonut pH={pH} pD={pD} pA={pA} home={fixture.home} away={fixture.away} />
        </div>
        <div className="sticker p-6">
          <h2 className="display text-xl mb-1 text-[color:var(--color-ink)]"><L es="MAPA DE MARCADORES" en="SCORE MAP" /></h2>
          <p data-l="en" className="text-xs text-[color:var(--color-ink-soft)] mb-4">Joint Poisson(λ_home, λ_away) with Dixon-Coles correction for low scores.</p>
          <p data-l="es" className="text-xs text-[color:var(--color-ink-soft)] mb-4">Poisson conjunta(λ_local, λ_visitante) con corrección de Dixon-Coles para marcadores bajos.</p>
          <ScoreHeatmap lambdaH={xgH} lambdaA={xgA} />
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-6 pb-16 grid sm:grid-cols-3 gap-4">
        <Card titleEn="Stadium" titleEs="Estadio">
          <div className="font-medium text-[color:var(--color-ink)]">{fixture.stadium}</div>
          <div className="text-sm text-[color:var(--color-ink-soft)]">{fixture.city}, {fixture.country}</div>
          <div data-l="en" className="text-xs text-[color:var(--color-ink-soft)] mt-2">Roof: {fixture.roof}{fixture.indoor ? " · indoor" : ""}</div>
          <div data-l="es" className="text-xs text-[color:var(--color-ink-soft)] mt-2">Techo: {fixture.roof}{fixture.indoor ? " · cubierto" : ""}</div>
        </Card>
        <Card titleEn="Altitude" titleEs="Altitud">
          <div className="display text-3xl tabular-nums text-[color:var(--color-ink)]">{fixture.altitude_m}m</div>
          <div data-l="en" className="text-xs text-[color:var(--color-ink-soft)] mt-1">{fixture.altitude_m > 1500 ? "Altitude penalty applied to unacclimatized teams" : "Negligible sea-level effect"}</div>
          <div data-l="es" className="text-xs text-[color:var(--color-ink-soft)] mt-1">{fixture.altitude_m > 1500 ? "Penalización por altitud aplicada a equipos no aclimatados" : "Efecto a nivel del mar despreciable"}</div>
        </Card>
        <Card titleEn="How to play it" titleEs="Cómo jugarla">
          <p data-l="en" className="text-sm text-[color:var(--color-ink)]">
            {pickEn.toLowerCase()}. The most likely scoreline in the joint distribution is approximately{" "}
            <span className="text-[color:var(--color-red)] font-bold">{Math.round(xgH)}–{Math.round(xgA)}</span>.
          </p>
          <p data-l="es" className="text-sm text-[color:var(--color-ink)]">
            {pickEs.toLowerCase()}. El marcador más probable en la distribución conjunta es aproximadamente{" "}
            <span className="text-[color:var(--color-red)] font-bold">{Math.round(xgH)}–{Math.round(xgA)}</span>.
          </p>
          <p data-l="en" className="text-xs text-[color:var(--color-ink-soft)] mt-2">Contrarian alternative: the draw at {fmtPct(pD)} if your Quiniela rewards upsets.</p>
          <p data-l="es" className="text-xs text-[color:var(--color-ink-soft)] mt-2">Alternativa a contracorriente: el empate a {fmtPct(pD)} si tu Quiniela premia las sorpresas.</p>
        </Card>
      </section>
    </div>
  );
}

function Card({ titleEn, titleEs, children }: { titleEn: string; titleEs: string; children: React.ReactNode }) {
  return (
    <div className="sticker p-5">
      <div className="display text-[10px] uppercase tracking-wider text-[color:var(--color-ink-soft)] mb-2"><L es={titleEs} en={titleEn} /></div>
      {children}
    </div>
  );
}
