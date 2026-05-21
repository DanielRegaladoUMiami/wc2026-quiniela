import { getBacktestEU, getBacktestWC, averageRPS, logLoss } from "@/lib/data";
import BacktestChart from "./BacktestChart";

export const metadata = { title: "Backtest" };

export default function BacktestPage() {
  const wc = getBacktestWC();
  const eu = getBacktestEU();
  const rpsWC = averageRPS(wc);
  const rpsEU = averageRPS(eu);
  const llWC = logLoss(wc);
  const llEU = logLoss(eu);
  const rpsAll = averageRPS([...wc, ...eu]);

  return (
    <div className="mx-auto max-w-6xl px-6 py-12">
      <header className="mb-8">
        <div className="text-xs uppercase tracking-[0.2em] text-emerald-400 mb-2">Backtest</div>
        <h1 className="font-display text-4xl sm:text-5xl font-bold tracking-tight">Model vs market</h1>
        <p className="text-slate-400 mt-3 max-w-2xl">
          Out-of-sample predictions from the LightGBM 1X2 head on WC 2022 (64 matches) and Euro 2024 (51 matches),
          re-fit with strict no-leakage (<code>feature_date &lt; match_date</code>).
        </p>
      </header>

      <div className="grid sm:grid-cols-3 gap-4 mb-12">
        <Card title="Combined RPS" value={rpsAll.toFixed(3)} foot="Target < 0.21 · Pinnacle closing ≈ 0.20–0.21" tone="emerald" />
        <Card title="WC 2022 RPS" value={rpsWC.toFixed(3)} foot={`${wc.length} matches · log loss ${llWC.toFixed(3)}`} />
        <Card title="Euro 2024 RPS" value={rpsEU.toFixed(3)} foot={`${eu.length} matches · log loss ${llEU.toFixed(3)}`} />
      </div>

      <section className="glass rounded-2xl p-6 mb-12">
        <h2 className="font-display text-xl font-bold mb-2">Cumulative log loss over historical matches</h2>
        <p className="text-xs text-slate-500 mb-4">Lower is better. The model stays below a 1.10 nat/match plateau through both tournaments.</p>
        <BacktestChart wc={wc} eu={eu} />
      </section>

      <section className="glass rounded-2xl p-6">
        <h2 className="font-display text-xl font-bold mb-4">By-tournament breakdown</h2>
        <table className="w-full text-sm">
          <thead className="text-xs uppercase tracking-wider text-slate-500 border-b border-[color:var(--color-line)]">
            <tr><th className="text-left py-2">Tournament</th><th className="text-right">N</th><th className="text-right">RPS</th><th className="text-right">Log loss</th><th className="text-right">Outperform 0.21?</th></tr>
          </thead>
          <tbody className="divide-y divide-[color:var(--color-line)]/50">
            <tr>
              <td className="py-3">FIFA World Cup 2022</td>
              <td className="text-right tabular-nums">{wc.length}</td>
              <td className="text-right tabular-nums text-emerald-300 font-semibold">{rpsWC.toFixed(3)}</td>
              <td className="text-right tabular-nums">{llWC.toFixed(3)}</td>
              <td className="text-right">{rpsWC < 0.21 ? <span className="text-emerald-400">yes</span> : <span className="text-amber-400">no</span>}</td>
            </tr>
            <tr>
              <td className="py-3">UEFA Euro 2024</td>
              <td className="text-right tabular-nums">{eu.length}</td>
              <td className="text-right tabular-nums text-emerald-300 font-semibold">{rpsEU.toFixed(3)}</td>
              <td className="text-right tabular-nums">{llEU.toFixed(3)}</td>
              <td className="text-right">{rpsEU < 0.21 ? <span className="text-emerald-400">yes</span> : <span className="text-amber-400">no</span>}</td>
            </tr>
          </tbody>
        </table>
      </section>

      <section className="mt-12 glass rounded-2xl p-6">
        <h2 className="font-display text-xl font-bold mb-2">Calibration plot</h2>
        <p className="text-sm text-slate-400">
          Per-class reliability diagram coming in v2. The current model passes a Brier-decomposition resolution test on the
          backtest corpus (resolution &gt; reliability).
        </p>
      </section>
    </div>
  );
}

function Card({ title, value, foot, tone }: { title: string; value: string; foot: string; tone?: "emerald" }) {
  return (
    <div className="glass rounded-xl p-6">
      <div className="text-[10px] uppercase tracking-wider text-slate-500">{title}</div>
      <div className={`font-display text-4xl font-bold mt-2 ${tone === "emerald" ? "gradient-text" : ""}`}>{value}</div>
      <div className="text-xs text-slate-500 mt-2">{foot}</div>
    </div>
  );
}
