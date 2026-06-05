import MathBlock from "./MathBlock";
import { getMeta } from "@/lib/data";

export const metadata = { title: "Methodology" };

export default function MethodologyPage() {
  return (
    <article className="mx-auto max-w-3xl px-6 py-16">
      <header className="sticker mb-10 overflow-hidden">
        <div className="halftone border-b-2 border-[color:var(--color-ink)] bg-[color:var(--color-red)] px-5 py-2">
          <span className="display text-sm text-[color:var(--color-card)]">METHOD · HOW THE ENSEMBLE WORKS</span>
        </div>
        <div className="p-5 sm:p-8">
          <div className="text-xs uppercase tracking-[0.2em] text-[color:var(--color-ink-soft)] mb-2">Methodology</div>
          <h1 className="display text-4xl sm:text-5xl text-[color:var(--color-ink)]">How the ensemble works</h1>
          <p className="text-[color:var(--color-ink-soft)] mt-3">
            Living document. Updated as models are implemented (Days 6–10 of the build plan).
          </p>
        </div>
      </header>

      <Section title="Goal">
        <p>
          Produce well-calibrated probabilistic predictions for every match of FIFA World Cup 2026, and convert them
          into pool-EV-optimal quiniela entries.
        </p>
      </Section>

      <Section title="1 · Dixon-Coles bivariate Poisson">
        <p>
          Classical model for football scorelines, fixing the under-prediction of low-score draws (0-0, 1-1) by a
          small correction parameter ρ. Fit with exponential time decay (ξ ≈ 0.0019 ≈ 1-year half-life) using{" "}
          <a className="text-[color:var(--color-red)] font-bold" href="https://github.com/martineastwood/penaltyblog">penaltyblog</a>.
        </p>
        <MathBlock>{String.raw`P(\text{home}=i, \text{away}=j) = \tau(i,j) \cdot \frac{e^{-\lambda_h}\lambda_h^i}{i!} \cdot \frac{e^{-\lambda_a}\lambda_a^j}{j!}`}</MathBlock>
      </Section>

      <Section title="2 · Hierarchical Bayesian Poisson (PyMC)">
        <p>Partial pooling regularizes sparse-data teams toward the overall mean. Host effects for USA / Mexico /
          Canada are estimated jointly — necessary because the 48-team / 3-host format has no historical precedent.</p>
        <MathBlock>{String.raw`\log \lambda_{home} = \mu + \alpha_{home} + \delta_{away} + \gamma(home, venue)`}</MathBlock>
        <MathBlock>{String.raw`\alpha, \delta \sim \mathcal{N}(0, \sigma); \quad \sigma \sim \text{HalfNormal}(1)`}</MathBlock>
      </Section>

      <Section title="3 · LightGBM">
        <p>Gradient-boosted classifiers on engineered features (Elo, FIFA rank, recent form, xG, squad value, venue,
          travel, altitude, rest). Tuned with Optuna under TimeSeriesSplit to prevent look-ahead.</p>
      </Section>

      <Section title="4 · Kalshi market features">
        <p>Implied probabilities (de-vigged with Shin&apos;s method) enter both as a stacker feature and as a benchmark
          to beat.</p>
      </Section>

      <Section title="5 · Stacker + calibration">
        <p>Multinomial logistic regression on out-of-fold base predictions + market features, followed by isotonic
          calibration per class.</p>
      </Section>

      <Section title="6 · Monte Carlo bracket">
        <p>{getMeta().n_sims.toLocaleString()} full-tournament simulations sampling scorelines from the calibrated joint distribution, with a
          penalty-shootout model for knockout draws.</p>
      </Section>

      <Section title="Anti-leakage protocol">
        <ul className="list-disc pl-5 space-y-1 text-[color:var(--color-ink)]">
          <li>All historical features stamped with <code className="font-mono text-[color:var(--color-red)]">feature_date &lt; match_date</code> (CI-enforced assertion).</li>
          <li>Elo reconstructed from per-match diffs, never current snapshot.</li>
          <li>FBref stats truncated to match date, not season totals.</li>
          <li>Transfermarkt values snapshotted by date.</li>
          <li>Historical-tournament backtests use Pinnacle closing odds.</li>
        </ul>
      </Section>

      <Section title="Metrics">
        <ul className="list-disc pl-5 space-y-1 text-[color:var(--color-ink)]">
          <li><strong>Ranked Probability Score (RPS)</strong> — primary, target &lt; 0.21.</li>
          <li>Log loss on 1X2.</li>
          <li>Brier on BTTS / Over 2.5.</li>
          <li>Reliability plots; ROI vs. Pinnacle closing.</li>
        </ul>
      </Section>
    </article>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="mt-10 first:mt-0">
      <h2 className="display text-2xl text-[color:var(--color-ink)] mb-3">{title}</h2>
      <div className="text-[color:var(--color-ink)] leading-relaxed space-y-3">{children}</div>
    </section>
  );
}
