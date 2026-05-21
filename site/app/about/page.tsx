export const metadata = { title: "About" };

export default function AboutPage() {
  return (
    <div className="mx-auto max-w-3xl px-6 py-16">
      <header className="mb-10">
        <div className="text-xs uppercase tracking-[0.2em] text-emerald-400 mb-2">About</div>
        <h1 className="font-display text-4xl sm:text-5xl font-bold tracking-tight">Why this project exists</h1>
      </header>

      <section className="space-y-5 text-slate-300 leading-relaxed">
        <p>
          Every four years, the world picks a World Cup champion in office pools using vibes, gut, and the team that
          made them happy in 2014. That&apos;s fine — pools are about fun. But there&apos;s an obvious gap:
          well-calibrated probabilities exist, they&apos;re just locked behind sportsbook spreadsheets or buried in
          academic papers.
        </p>
        <p>
          This project closes that gap with a transparent four-model ensemble — Dixon-Coles, a hierarchical Bayesian
          Poisson, gradient boosting, and Kalshi market features — stacked, isotonically calibrated, and propagated
          through 50,000 Monte Carlo bracket simulations.
        </p>
        <p>
          Everything is reproducible. The repository ships the data fetchers, the model fits, the backtest harness
          with anti-leakage CI assertions, and a strategy layer that maximizes <em>expected pool points</em> (not
          argmax). Pool format and scoring rubric are configurable.
        </p>

        <h2 className="font-display text-2xl font-bold tracking-tight mt-10">Author</h2>
        <p>
          <strong className="text-slate-100">Daniel Regalado</strong>. MS Business Analytics, University of Miami.
          Bilingual ES/EN. Find me on{" "}
          <a className="text-emerald-400 hover:underline" href="https://github.com/DanielRegaladoUMiami">GitHub</a>{" "}
          or read the{" "}
          <a className="text-emerald-400 hover:underline" href="/methodology">methodology</a>.
        </p>

        <h2 className="font-display text-2xl font-bold tracking-tight mt-10">License & disclaimer</h2>
        <p className="text-slate-400 text-sm">
          Apache 2.0. The Gradio dashboard lives on Hugging Face Spaces; the static site you&apos;re reading is the
          production front-end. Not financial advice. Models are wrong; some are useful.
        </p>
      </section>
    </div>
  );
}
