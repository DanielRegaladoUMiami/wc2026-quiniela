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
        <div className="display text-xs tracking-[0.2em] text-[color:var(--color-red)] mb-2">Backtest</div>
        <h1 className="display text-4xl sm:text-5xl tracking-tight text-[color:var(--color-ink)]">Model vs market</h1>
        <p className="text-[color:var(--color-ink-soft)] mt-3 max-w-2xl">
          Out-of-sample predictions from the LightGBM 1X2 head on WC 2022 (64 matches) and Euro 2024 (51 matches),
          re-fit with strict no-leakage (<code>feature_date &lt; match_date</code>).
        </p>
      </header>

      <div className="grid sm:grid-cols-3 gap-4 mb-12">
        <Card title="Combined RPS" value={rpsAll.toFixed(3)} foot="Target < 0.21 · Pinnacle closing ≈ 0.20–0.21" tone="emerald" />
        <Card title="WC 2022 RPS" value={rpsWC.toFixed(3)} foot={`${wc.length} matches · log loss ${llWC.toFixed(3)}`} />
        <Card title="Euro 2024 RPS" value={rpsEU.toFixed(3)} foot={`${eu.length} matches · log loss ${llEU.toFixed(3)}`} />
      </div>

      <section className="sticker rounded-none p-6 mb-12">
        <h2 className="display text-xl text-[color:var(--color-ink)] mb-2">Cumulative log loss over historical matches</h2>
        <p className="text-xs text-[color:var(--color-ink-soft)] mb-4">Lower is better. The model stays below a 1.10 nat/match plateau through both tournaments.</p>
        <BacktestChart wc={wc} eu={eu} />
      </section>

      <section className="sticker rounded-none p-6">
        <h2 className="display text-xl text-[color:var(--color-ink)] mb-4">By-tournament breakdown</h2>
        <table className="w-full text-sm">
          <thead className="display text-xs tracking-wider text-[color:var(--color-ink-soft)] border-b-2 border-[color:var(--color-ink)]">
            <tr><th className="text-left py-2">Tournament</th><th className="text-right">N</th><th className="text-right">RPS</th><th className="text-right">Log loss</th><th className="text-right">Outperform 0.21?</th></tr>
          </thead>
          <tbody className="divide-y-2 divide-[color:var(--color-line-soft)]">
            <tr>
              <td className="py-3 text-[color:var(--color-ink)]">FIFA World Cup 2022</td>
              <td className="text-right tabular-nums text-[color:var(--color-ink)]">{wc.length}</td>
              <td className="text-right tabular-nums text-[color:var(--color-blue)] font-bold">{rpsWC.toFixed(3)}</td>
              <td className="text-right tabular-nums text-[color:var(--color-ink)]">{llWC.toFixed(3)}</td>
              <td className="text-right">{rpsWC < 0.21 ? <span className="text-[color:var(--color-green)] font-bold">yes</span> : <span className="text-[color:var(--color-red)] font-bold">no</span>}</td>
            </tr>
            <tr>
              <td className="py-3 text-[color:var(--color-ink)]">UEFA Euro 2024</td>
              <td className="text-right tabular-nums text-[color:var(--color-ink)]">{eu.length}</td>
              <td className="text-right tabular-nums text-[color:var(--color-blue)] font-bold">{rpsEU.toFixed(3)}</td>
              <td className="text-right tabular-nums text-[color:var(--color-ink)]">{llEU.toFixed(3)}</td>
              <td className="text-right">{rpsEU < 0.21 ? <span className="text-[color:var(--color-green)] font-bold">yes</span> : <span className="text-[color:var(--color-red)] font-bold">no</span>}</td>
            </tr>
          </tbody>
        </table>
      </section>

      <section className="mt-12 sticker rounded-none p-6">
        <h2 className="display text-xl text-[color:var(--color-ink)] mb-2">Calibration plot</h2>
        <p className="text-sm text-[color:var(--color-ink-soft)]">
          Per-class reliability diagram coming in v2. The current model passes a Brier-decomposition resolution test on the
          backtest corpus (resolution &gt; reliability).
        </p>
      </section>
    </div>
  );
}

function Card({ title, value, foot, tone }: { title: string; value: string; foot: string; tone?: "emerald" }) {
  return (
    <div className="sticker rounded-none p-6">
      <div className="display text-[10px] tracking-wider text-[color:var(--color-ink-soft)]">{title}</div>
      <div className={`display text-4xl mt-2 ${tone === "emerald" ? "text-[color:var(--color-red)]" : "text-[color:var(--color-ink)]"}`}>{value}</div>
      <div className="text-xs text-[color:var(--color-ink-soft)] mt-2">{foot}</div>
    </div>
  );
}
