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
      <div className="absolute inset-0 -z-10">
        <div className="absolute top-[-20%] right-[-10%] h-[600px] w-[600px] rounded-full bg-emerald-500/20 blur-[120px]" />
        <div className="absolute bottom-[-30%] left-[-10%] h-[500px] w-[500px] rounded-full bg-amber-400/10 blur-[120px]" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_0%,rgba(255,255,255,0.04),transparent_60%)]" />
      </div>
      <div className="mx-auto max-w-7xl px-6 pt-20 pb-16 sm:pt-28 sm:pb-24">
        <div className="flex flex-col items-start gap-6 max-w-3xl">
          <span className="inline-flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/5 px-3 py-1 text-xs text-emerald-300">
            <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-emerald-400" />
            Updated {meta.generated_at.slice(0, 10)} · {meta.sim_run}
          </span>

          <h1 className="font-display text-5xl sm:text-7xl font-bold tracking-tighter leading-[0.95]">
            The math behind <br />
            <span className="gradient-text">the 2026 World Cup.</span>
          </h1>

          <p className="text-lg text-slate-300 max-w-2xl leading-relaxed">
            Open-source probabilistic predictions for every match of the FIFA World Cup 2026.
            A four-model ensemble, Monte Carlo bracket, and pool-EV optimizer — all transparent and reproducible.
          </p>

          <Countdown />

          <div className="flex flex-wrap gap-3 pt-2">
            <Link
              href="/bracket"
              className="inline-flex items-center gap-2 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 px-5 py-2.5 text-sm font-semibold transition-colors"
            >
              Explore the bracket
              <span aria-hidden>→</span>
            </Link>
            <Link
              href="/methodology"
              className="inline-flex items-center rounded-lg border border-[color:var(--color-line)] hover:border-emerald-500/40 hover:bg-white/5 px-5 py-2.5 text-sm font-medium transition-colors"
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
      <div className="font-display text-2xl sm:text-3xl font-bold tabular-nums">{n}</div>
      <div className="text-xs text-slate-500 mt-0.5">{label}</div>
      {sub && <div className="text-[10px] text-emerald-400 mt-0.5">{sub}</div>}
    </div>
  );
}
