import { getMeta } from "@/lib/data";

export const metadata = { title: "About" };

export default function AboutPage() {
  return (
    <div className="mx-auto max-w-3xl px-6 py-16">
      <header className="mb-10">
        <div className="display text-xs tracking-[0.2em] text-[color:var(--color-red)] mb-2">About</div>
        <h1 className="display text-4xl sm:text-5xl tracking-tight text-[color:var(--color-ink)]">Why this project exists</h1>
      </header>

      <section className="space-y-5 text-[color:var(--color-ink)] leading-relaxed">
        <p>
          Every four years, the world picks a World Cup champion in office pools using vibes, gut, and the team that
          made them happy in 2014. That&apos;s fine — pools are about fun. But there&apos;s an obvious gap:
          well-calibrated probabilities exist, they&apos;re just locked behind sportsbook spreadsheets or buried in
          academic papers.
        </p>
        <p>
          This project closes that gap with a transparent four-model ensemble — Dixon-Coles, a hierarchical Bayesian
          Poisson, gradient boosting, and Kalshi market features — stacked, isotonically calibrated, and propagated
          through {getMeta().n_sims.toLocaleString()} Monte Carlo bracket simulations.
        </p>
        <p>
          Everything is reproducible. The repository ships the data fetchers, the model fits, the backtest harness
          with anti-leakage CI assertions, and a strategy layer that maximizes <em>expected pool points</em> (not
          argmax). Pool format and scoring rubric are configurable.
        </p>

        <h2 className="display text-2xl tracking-tight mt-10 text-[color:var(--color-ink)]">Author</h2>
        <p>
          <strong className="text-[color:var(--color-ink)]">Daniel Regalado</strong>. MS Business Analytics, University of Miami.
          Bilingual ES/EN. Find me on{" "}
          <a className="text-[color:var(--color-red)] hover:underline" href="https://github.com/DanielRegaladoUMiami">GitHub</a>{" "}
          or read the{" "}
          <a className="text-[color:var(--color-red)] hover:underline" href="/methodology">methodology</a>.
        </p>

        <h2 className="display text-2xl tracking-tight mt-10 text-[color:var(--color-ink)]">License & disclaimer</h2>
        <p className="text-[color:var(--color-ink-soft)] text-sm">
          Apache 2.0. The Gradio dashboard lives on Hugging Face Spaces; the static site you&apos;re reading is the
          production front-end. Not financial advice. Models are wrong; some are useful.
        </p>
      </section>
    </div>
  );
}
