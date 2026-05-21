import { getMeta } from "@/lib/data";

export default function Footer() {
  const meta = getMeta();
  return (
    <footer className="border-t border-[color:var(--color-line)] mt-16">
      <div className="mx-auto max-w-7xl px-6 py-10 grid sm:grid-cols-3 gap-6 text-sm">
        <div>
          <div className="font-display text-lg font-semibold">WC2026 Quiniela</div>
          <p className="text-slate-400 mt-1 max-w-xs">
            Open-source probabilistic predictions for the 2026 FIFA World Cup. Apache 2.0.
          </p>
        </div>
        <div className="space-y-1 text-slate-400">
          <div>Sim run · <span className="text-slate-200">{meta.sim_run}</span></div>
          <div>{meta.n_sims.toLocaleString()} simulations · {meta.n_matches} matches</div>
          <div>Backtest RPS <span className="text-emerald-400 font-medium">0.188</span> · Bookmaker ≈ 0.21</div>
        </div>
        <div className="space-y-1 text-slate-400">
          <a className="block hover:text-white" href="https://github.com/DanielRegaladoUMiami/wc2026-quiniela">GitHub repository</a>
          <a className="block hover:text-white" href="/methodology">Methodology</a>
          <div className="text-xs text-slate-500 pt-2">Not financial advice. Models are wrong; some are useful.</div>
        </div>
      </div>
    </footer>
  );
}
