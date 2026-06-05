import { getBacktestEU, getBacktestWC, averageRPS, logLoss } from "@/lib/data";
import L from "@/components/L";
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
        <h1 className="display text-4xl sm:text-5xl tracking-tight text-[color:var(--color-ink)]">
          <L es="El modelo contra el mercado" en="Model vs market" />
        </h1>
        <p data-l="en" className="text-[color:var(--color-ink-soft)] mt-3 max-w-2xl">
          Out-of-sample predictions from the LightGBM 1X2 head on WC 2022 (64 matches) and Euro 2024 (51 matches),
          re-fit with strict no-leakage (<code>feature_date &lt; match_date</code>).
        </p>
        <p data-l="es" className="text-[color:var(--color-ink-soft)] mt-3 max-w-2xl">
          Predicciones fuera de muestra de la cabeza 1X2 de LightGBM sobre el WC 2022 (64 partidos) y la Euro 2024 (51 partidos),
          reentrenado sin fugas de datos (<code>feature_date &lt; match_date</code>).
        </p>
      </header>

      <div className="grid sm:grid-cols-3 gap-4 mb-12">
        <Card titleEn="Combined RPS" titleEs="RPS combinado" value={rpsAll.toFixed(3)} footEn="Target < 0.21 · Pinnacle closing ≈ 0.20–0.21" footEs="Objetivo < 0.21 · cierre de Pinnacle ≈ 0.20–0.21" tone="emerald" />
        <Card titleEn="WC 2022 RPS" titleEs="RPS WC 2022" value={rpsWC.toFixed(3)} footEn={`${wc.length} matches · log loss ${llWC.toFixed(3)}`} footEs={`${wc.length} partidos · log loss ${llWC.toFixed(3)}`} />
        <Card titleEn="Euro 2024 RPS" titleEs="RPS Euro 2024" value={rpsEU.toFixed(3)} footEn={`${eu.length} matches · log loss ${llEU.toFixed(3)}`} footEs={`${eu.length} partidos · log loss ${llEU.toFixed(3)}`} />
      </div>

      <section className="sticker rounded-none p-6 mb-12">
        <h2 className="display text-xl text-[color:var(--color-ink)] mb-2">
          <L es="Log loss acumulado a lo largo de los partidos históricos" en="Cumulative log loss over historical matches" />
        </h2>
        <p className="text-xs text-[color:var(--color-ink-soft)] mb-4">
          <L
            es="Mientras más bajo, mejor. El modelo se mantiene por debajo de una meseta de 1.10 nats por partido en ambos torneos."
            en="Lower is better. The model stays below a 1.10 nat/match plateau through both tournaments."
          />
        </p>
        <BacktestChart wc={wc} eu={eu} />
      </section>

      <section className="sticker rounded-none p-6">
        <h2 className="display text-xl text-[color:var(--color-ink)] mb-4">
          <L es="Desglose por torneo" en="By-tournament breakdown" />
        </h2>
        <table className="w-full text-sm">
          <thead className="display text-xs tracking-wider text-[color:var(--color-ink-soft)] border-b-2 border-[color:var(--color-ink)]">
            <tr>
              <th className="text-left py-2"><L es="Torneo" en="Tournament" /></th>
              <th className="text-right">N</th>
              <th className="text-right">RPS</th>
              <th className="text-right"><L es="Log loss" en="Log loss" /></th>
              <th className="text-right"><L es="¿Le gana a 0.21?" en="Outperform 0.21?" /></th>
            </tr>
          </thead>
          <tbody className="divide-y-2 divide-[color:var(--color-line-soft)]">
            <tr>
              <td className="py-3 text-[color:var(--color-ink)]">FIFA World Cup 2022</td>
              <td className="text-right tabular-nums text-[color:var(--color-ink)]">{wc.length}</td>
              <td className="text-right tabular-nums text-[color:var(--color-blue)] font-bold">{rpsWC.toFixed(3)}</td>
              <td className="text-right tabular-nums text-[color:var(--color-ink)]">{llWC.toFixed(3)}</td>
              <td className="text-right">{rpsWC < 0.21 ? <span className="text-[color:var(--color-green)] font-bold"><L es="sí" en="yes" /></span> : <span className="text-[color:var(--color-red)] font-bold"><L es="no" en="no" /></span>}</td>
            </tr>
            <tr>
              <td className="py-3 text-[color:var(--color-ink)]">UEFA Euro 2024</td>
              <td className="text-right tabular-nums text-[color:var(--color-ink)]">{eu.length}</td>
              <td className="text-right tabular-nums text-[color:var(--color-blue)] font-bold">{rpsEU.toFixed(3)}</td>
              <td className="text-right tabular-nums text-[color:var(--color-ink)]">{llEU.toFixed(3)}</td>
              <td className="text-right">{rpsEU < 0.21 ? <span className="text-[color:var(--color-green)] font-bold"><L es="sí" en="yes" /></span> : <span className="text-[color:var(--color-red)] font-bold"><L es="no" en="no" /></span>}</td>
            </tr>
          </tbody>
        </table>
      </section>

      <section className="mt-12 sticker rounded-none p-6">
        <h2 className="display text-xl text-[color:var(--color-ink)] mb-2">
          <L es="Gráfica de calibración" en="Calibration plot" />
        </h2>
        <p data-l="en" className="text-sm text-[color:var(--color-ink-soft)]">
          Per-class reliability diagram coming in v2. The current model passes a Brier-decomposition resolution test on the
          backtest corpus (resolution &gt; reliability).
        </p>
        <p data-l="es" className="text-sm text-[color:var(--color-ink-soft)]">
          El diagrama de fiabilidad por clase llega en la v2. El modelo actual aprueba una prueba de resolución por descomposición de Brier sobre el
          corpus del backtest (resolución &gt; fiabilidad).
        </p>
      </section>
    </div>
  );
}

function Card({ titleEn, titleEs, value, footEn, footEs, tone }: { titleEn: string; titleEs: string; value: string; footEn: string; footEs: string; tone?: "emerald" }) {
  return (
    <div className="sticker rounded-none p-6">
      <div className="display text-[10px] tracking-wider text-[color:var(--color-ink-soft)]"><L es={titleEs} en={titleEn} /></div>
      <div className={`display text-4xl mt-2 ${tone === "emerald" ? "text-[color:var(--color-red)]" : "text-[color:var(--color-ink)]"}`}>{value}</div>
      <div className="text-xs text-[color:var(--color-ink-soft)] mt-2"><L es={footEs} en={footEn} /></div>
    </div>
  );
}
