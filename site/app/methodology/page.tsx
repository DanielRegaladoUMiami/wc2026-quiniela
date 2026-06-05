import MathBlock from "./MathBlock";
import L from "@/components/L";
import { getMeta } from "@/lib/data";

export const metadata = { title: "Methodology" };

export default function MethodologyPage() {
  return (
    <article className="mx-auto max-w-3xl px-6 py-16">
      <header className="sticker mb-10 overflow-hidden">
        <div className="halftone border-b-2 border-[color:var(--color-ink)] bg-[color:var(--color-red)] px-5 py-2">
          <span className="display text-sm text-[color:var(--color-card)]">
            <L es="MÉTODO · CÓMO FUNCIONA EL ENSEMBLE" en="METHOD · HOW THE ENSEMBLE WORKS" />
          </span>
        </div>
        <div className="p-5 sm:p-8">
          <div className="text-xs uppercase tracking-[0.2em] text-[color:var(--color-ink-soft)] mb-2">
            <L es="Metodología" en="Methodology" />
          </div>
          <h1 className="display text-4xl sm:text-5xl text-[color:var(--color-ink)]">
            <L es="Cómo funciona el ensemble" en="How the ensemble works" />
          </h1>
          <p className="text-[color:var(--color-ink-soft)] mt-3">
            <L
              es="Documento vivo. Se actualiza a medida que se implementan los modelos (días 6–10 del plan de desarrollo)."
              en="Living document. Updated as models are implemented (Days 6–10 of the build plan)."
            />
          </p>
        </div>
      </header>

      <Section titleEn="Goal" titleEs="Objetivo">
        <p data-l="en">
          Produce well-calibrated probabilistic predictions for every match of FIFA World Cup 2026, and convert them
          into pool-EV-optimal quiniela entries.
        </p>
        <p data-l="es">
          Producir predicciones probabilísticas bien calibradas para cada partido del Mundial de la FIFA 2026, y
          convertirlas en entradas de Quiniela óptimas en valor esperado del pozo.
        </p>
      </Section>

      <Section titleEn="1 · Dixon-Coles bivariate Poisson" titleEs="1 · Poisson bivariado Dixon-Coles">
        <p data-l="en">
          Classical model for football scorelines, fixing the under-prediction of low-score draws (0-0, 1-1) by a
          small correction parameter ρ. Fit with exponential time decay (ξ ≈ 0.0019 ≈ 1-year half-life) using{" "}
          <a className="text-[color:var(--color-red)] font-bold" href="https://github.com/martineastwood/penaltyblog">penaltyblog</a>.
        </p>
        <p data-l="es">
          Modelo clásico para marcadores de fútbol, que corrige la subestimación de los empates de pocos goles (0-0,
          1-1) mediante un pequeño parámetro de corrección ρ. Ajustado con decaimiento temporal exponencial (ξ ≈ 0.0019
          ≈ vida media de 1 año) usando{" "}
          <a className="text-[color:var(--color-red)] font-bold" href="https://github.com/martineastwood/penaltyblog">penaltyblog</a>.
        </p>
        <MathBlock>{String.raw`P(\text{home}=i, \text{away}=j) = \tau(i,j) \cdot \frac{e^{-\lambda_h}\lambda_h^i}{i!} \cdot \frac{e^{-\lambda_a}\lambda_a^j}{j!}`}</MathBlock>
      </Section>

      <Section titleEn="2 · Hierarchical Bayesian Poisson (PyMC)" titleEs="2 · Poisson bayesiano jerárquico (PyMC)">
        <p data-l="en">Partial pooling regularizes sparse-data teams toward the overall mean. Host effects for USA / Mexico /
          Canada are estimated jointly — necessary because the 48-team / 3-host format has no historical precedent.</p>
        <p data-l="es">El pooling parcial regulariza a los equipos con pocos datos hacia la media general. Los efectos de local para
          USA / México / Canadá se estiman conjuntamente — necesario porque el formato de 48 equipos y 3 sedes no tiene precedente histórico.</p>
        <MathBlock>{String.raw`\log \lambda_{home} = \mu + \alpha_{home} + \delta_{away} + \gamma(home, venue)`}</MathBlock>
        <MathBlock>{String.raw`\alpha, \delta \sim \mathcal{N}(0, \sigma); \quad \sigma \sim \text{HalfNormal}(1)`}</MathBlock>
      </Section>

      <Section titleEn="3 · LightGBM" titleEs="3 · LightGBM">
        <p data-l="en">Gradient-boosted classifiers on engineered features (Elo, FIFA rank, recent form, xG, squad value, venue,
          travel, altitude, rest). Tuned with Optuna under TimeSeriesSplit to prevent look-ahead.</p>
        <p data-l="es">Clasificadores con gradient boosting sobre features diseñadas (Elo, ranking FIFA, forma reciente, xG, valor de plantilla, sede,
          viajes, altitud, descanso). Optimizados con Optuna bajo TimeSeriesSplit para evitar el look-ahead.</p>
      </Section>

      <Section titleEn="4 · Kalshi market features" titleEs="4 · Features de mercado de Kalshi">
        <p data-l="en">Implied probabilities (de-vigged with Shin&apos;s method) enter both as a stacker feature and as a benchmark
          to beat.</p>
        <p data-l="es">Las probabilidades implícitas (sin la comisión, con el método de Shin) entran tanto como feature del stacker como benchmark
          a vencer.</p>
      </Section>

      <Section titleEn="5 · Stacker + calibration" titleEs="5 · Stacker + calibración">
        <p data-l="en">Multinomial logistic regression on out-of-fold base predictions + market features, followed by isotonic
          calibration per class.</p>
        <p data-l="es">Regresión logística multinomial sobre las predicciones base out-of-fold + features de mercado, seguida de calibración isotónica
          por clase.</p>
      </Section>

      <Section titleEn="6 · Monte Carlo bracket" titleEs="6 · Bracket Monte Carlo">
        <p data-l="en">{getMeta().n_sims.toLocaleString()} full-tournament simulations sampling scorelines from the calibrated joint distribution, with a
          penalty-shootout model for knockout draws.</p>
        <p data-l="es">{getMeta().n_sims.toLocaleString()} simulaciones del torneo completo que muestrean marcadores de la distribución conjunta calibrada, con un
          modelo de tanda de penales para los empates de eliminatoria.</p>
      </Section>

      <Section titleEn="Anti-leakage protocol" titleEs="Protocolo anti-leakage">
        <ul data-l="en" className="list-disc pl-5 space-y-1 text-[color:var(--color-ink)]">
          <li>All historical features stamped with <code className="font-mono text-[color:var(--color-red)]">feature_date &lt; match_date</code> (CI-enforced assertion).</li>
          <li>Elo reconstructed from per-match diffs, never current snapshot.</li>
          <li>FBref stats truncated to match date, not season totals.</li>
          <li>Transfermarkt values snapshotted by date.</li>
          <li>Historical-tournament backtests use Pinnacle closing odds.</li>
        </ul>
        <ul data-l="es" className="list-disc pl-5 space-y-1 text-[color:var(--color-ink)]">
          <li>Todas las features históricas se sellan con <code className="font-mono text-[color:var(--color-red)]">feature_date &lt; match_date</code> (aserción validada en CI).</li>
          <li>El Elo se reconstruye a partir de las diferencias por partido, nunca del snapshot actual.</li>
          <li>Las estadísticas de FBref se truncan a la fecha del partido, no a los totales de la temporada.</li>
          <li>Los valores de Transfermarkt se capturan por fecha.</li>
          <li>Los backtests de torneos históricos usan las cuotas de cierre de Pinnacle.</li>
        </ul>
      </Section>

      <Section titleEn="Metrics" titleEs="Métricas">
        <ul data-l="en" className="list-disc pl-5 space-y-1 text-[color:var(--color-ink)]">
          <li><strong>Ranked Probability Score (RPS)</strong> — primary, target &lt; 0.21.</li>
          <li>Log loss on 1X2.</li>
          <li>Brier on BTTS / Over 2.5.</li>
          <li>Reliability plots; ROI vs. Pinnacle closing.</li>
        </ul>
        <ul data-l="es" className="list-disc pl-5 space-y-1 text-[color:var(--color-ink)]">
          <li><strong>Ranked Probability Score (RPS)</strong> — principal, objetivo &lt; 0.21.</li>
          <li>Log loss en 1X2.</li>
          <li>Brier en BTTS / Más de 2.5.</li>
          <li>Gráficas de confiabilidad; ROI vs. cierre de Pinnacle.</li>
        </ul>
      </Section>
    </article>
  );
}

function Section({
  titleEn,
  titleEs,
  children,
}: {
  titleEn: string;
  titleEs: string;
  children: React.ReactNode;
}) {
  return (
    <section className="mt-10 first:mt-0">
      <h2 className="display text-2xl text-[color:var(--color-ink)] mb-3">
        <L es={titleEs} en={titleEn} />
      </h2>
      <div className="text-[color:var(--color-ink)] leading-relaxed space-y-3">{children}</div>
    </section>
  );
}
