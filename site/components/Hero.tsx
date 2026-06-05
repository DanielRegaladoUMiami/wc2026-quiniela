import Link from "next/link";
import Countdown from "./Countdown";
import { getMeta, getBacktestWC, getBacktestEU, averageRPS } from "@/lib/data";

export default function Hero() {
  const meta = getMeta();
  // Compute the headline RPS from the same shipped backtest data as /backtest —
  // never hardcode it, so Hero and the Backtest page can never disagree.
  const rpsAll = averageRPS([...getBacktestWC(), ...getBacktestEU()]);
  return (
    <section className="relative overflow-hidden">
      <div className="mx-auto max-w-7xl px-6 pt-20 pb-16 sm:pt-28 sm:pb-24">
        <div className="flex flex-col items-start gap-6 max-w-3xl">
          <span className="inline-flex items-center gap-2 border-2 border-[color:var(--color-ink)] bg-[color:var(--color-yellow)] px-3 py-1 text-xs display text-[color:var(--color-ink)]">
            <span className="relative inline-flex h-1.5 w-1.5 bg-[color:var(--color-red)] border border-[color:var(--color-ink)]" />
            Updated {meta.generated_at.slice(0, 10)} · {meta.sim_run}
          </span>

          <h1 className="display text-5xl sm:text-7xl leading-[0.95] text-[color:var(--color-ink)]">
            The math behind <br />
            <span className="text-[color:var(--color-red)]">the 2026 World Cup.</span>
          </h1>

          <p className="text-lg text-[color:var(--color-ink-soft)] max-w-2xl leading-relaxed">
            Open-source probabilistic predictions for every match of the FIFA World Cup 2026.
            A four-model ensemble, Monte Carlo bracket, and pool-EV optimizer — all transparent and reproducible.
          </p>

          <Countdown />

          <div className="flex flex-wrap gap-3 pt-2">
            <Link
              href="/bracket"
              className="display inline-flex items-center gap-2 rounded-none bg-[color:var(--color-blue)] border-2 border-[color:var(--color-ink)] text-[color:var(--color-card)] hover:bg-[color:var(--color-ink)] hover:text-[color:var(--color-yellow)] px-5 py-2.5 text-sm transition-colors"
            >
              Explore the bracket
              <span aria-hidden>→</span>
            </Link>
            <Link
              href="/methodology"
              className="display inline-flex items-center rounded-none border-2 border-[color:var(--color-ink)] bg-[color:var(--color-yellow)] text-[color:var(--color-ink)] hover:bg-[color:var(--color-ink)] hover:text-[color:var(--color-yellow)] px-5 py-2.5 text-sm transition-colors"
            >
              How it works
            </Link>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 sm:gap-8 pt-8 w-full sm:w-auto">
            <Stat n={meta.n_matches} label="Matches modeled" />
            <Stat n={`${(meta.n_sims).toLocaleString()}×`} label="Sims per match" />
            <Stat n={`${(meta.n_sims * meta.n_matches / 1000).toFixed(0)}k`} label="Outcomes" />
            <Stat n={rpsAll.toFixed(3)} label="Backtest RPS" sub="vs ~0.21 market" />
          </div>
        </div>
      </div>
    </section>
  );
}

function Stat({ n, label, sub }: { n: number | string; label: string; sub?: string }) {
  return (
    <div>
      <div className="display text-2xl sm:text-3xl tabular-nums text-[color:var(--color-ink)]">{n}</div>
      <div className="text-xs text-[color:var(--color-ink-soft)] mt-0.5">{label}</div>
      {sub && <div className="text-[10px] text-[color:var(--color-red)] mt-0.5">{sub}</div>}
    </div>
  );
}
