import { getAdvancement, getTeams, fmtPct } from "@/lib/data";
import BracketSVG from "@/components/BracketSVG";

export const metadata = { title: "Bracket" };

export default function BracketPage() {
  const adv = getAdvancement();
  const teams = getTeams();

  const sorted = [...adv].sort((a, b) => b.p_champion - a.p_champion);

  return (
    <div className="mx-auto max-w-7xl px-6 py-12">
      <header className="mb-8">
        <h1 className="font-display text-4xl sm:text-5xl font-bold tracking-tight">Probabilistic bracket</h1>
        <p className="text-slate-400 mt-2 max-w-2xl">
          Per-round survival rates from 5,000 Monte Carlo simulations. Reading: P(reach Round of 16) →
          P(reach Quarterfinal) → … → P(lift the trophy).
        </p>
      </header>

      <div className="glass rounded-2xl p-6 overflow-x-auto">
        <BracketSVG advancement={sorted.slice(0, 16)} teams={teams} />
      </div>

      <section className="grid sm:grid-cols-2 gap-6 mt-12">
        <Stat
          title="Most concentrated favorite"
          subtitle={sorted[0].team}
          value={fmtPct(sorted[0].p_champion)}
          tone="emerald"
        />
        <Stat
          title="Best dark horse (top 12)"
          subtitle={sorted.slice(6, 12).reduce((a, b) => (b.p_champion > a.p_champion ? b : a), sorted[6]).team}
          value={fmtPct(sorted.slice(6, 12).reduce((a, b) => (b.p_champion > a.p_champion ? b : a), sorted[6]).p_champion)}
          tone="amber"
        />
      </section>
    </div>
  );
}

function Stat({ title, subtitle, value, tone }: { title: string; subtitle: string; value: string; tone: "emerald" | "amber" }) {
  const cls = tone === "emerald" ? "text-emerald-300" : "text-amber-300";
  return (
    <div className="glass rounded-xl p-6">
      <div className="text-[10px] uppercase tracking-wider text-slate-500">{title}</div>
      <div className="font-display text-3xl font-bold mt-2">{subtitle}</div>
      <div className={`font-display text-5xl font-bold mt-1 ${cls}`}>{value}</div>
    </div>
  );
}
