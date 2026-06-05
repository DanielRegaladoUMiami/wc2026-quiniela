import { getAdvancement, getTeams, getMeta, fmtPct } from "@/lib/data";
import BracketSVG from "@/components/BracketSVG";

export const metadata = { title: "Bracket" };

export default function BracketPage() {
  const adv = getAdvancement();
  const teams = getTeams();

  const sorted = [...adv].sort((a, b) => b.p_champion - a.p_champion);

  return (
    <div className="mx-auto max-w-7xl px-6 py-12">
      <header className="mb-8">
        <h1 className="display text-4xl sm:text-5xl text-[color:var(--color-ink)]">Probabilistic bracket</h1>
        <p className="text-[color:var(--color-ink-soft)] mt-2 max-w-2xl">
          Per-round survival rates from {getMeta().n_sims.toLocaleString()} Monte Carlo simulations. Reading: P(reach Round of 16) →
          P(reach Quarterfinal) → … → P(lift the trophy).
        </p>
      </header>

      <div className="sticker p-6 overflow-x-auto">
        <BracketSVG advancement={sorted.slice(0, 16)} teams={teams} />
      </div>

      <section className="grid sm:grid-cols-2 gap-6 mt-12">
        <Stat
          title="Most concentrated favorite"
          subtitle={sorted[0].team}
          value={fmtPct(sorted[0].p_champion)}
          tone="red"
        />
        <Stat
          title="Best dark horse (top 12)"
          subtitle={sorted.slice(6, 12).reduce((a, b) => (b.p_champion > a.p_champion ? b : a), sorted[6]).team}
          value={fmtPct(sorted.slice(6, 12).reduce((a, b) => (b.p_champion > a.p_champion ? b : a), sorted[6]).p_champion)}
          tone="yellow"
        />
      </section>
    </div>
  );
}

function Stat({ title, subtitle, value, tone }: { title: string; subtitle: string; value: string; tone: "red" | "yellow" }) {
  const cls = tone === "red" ? "text-[color:var(--color-red)]" : "text-[color:var(--color-yellow)]";
  return (
    <div className="sticker p-6">
      <div className="display text-[10px] tracking-wider text-[color:var(--color-ink-soft)]">{title}</div>
      <div className="display text-3xl mt-2 text-[color:var(--color-ink)]">{subtitle}</div>
      <div className={`display text-5xl mt-1 ${cls}`}>{value}</div>
    </div>
  );
}
