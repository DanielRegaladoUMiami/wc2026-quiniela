import L from "@/components/L";
import { getMeta } from "@/lib/data";

export const metadata = { title: "About" };

export default function AboutPage() {
  return (
    <div className="mx-auto max-w-3xl px-6 py-16">
      <header className="mb-10">
        <div className="display text-xs tracking-[0.2em] text-[color:var(--color-red)] mb-2">
          <L es="Acerca de" en="About" />
        </div>
        <h1 className="display text-4xl sm:text-5xl tracking-tight text-[color:var(--color-ink)]">
          <L es="Por qué existe este proyecto" en="Why this project exists" />
        </h1>
      </header>

      <section className="space-y-5 text-[color:var(--color-ink)] leading-relaxed">
        <p>
          <L
            es="Cada cuatro años, el mundo elige al campeón del Mundial en las quinielas de la oficina a punta de corazonadas, intuición y el equipo que los hizo felices en 2014. Y está bien — las quinielas son para divertirse. Pero hay un vacío evidente: las probabilidades bien calibradas existen, solo que están encerradas en las hojas de cálculo de las casas de apuestas o enterradas en papers académicos."
            en="Every four years, the world picks a World Cup champion in office pools using vibes, gut, and the team that made them happy in 2014. That's fine — pools are about fun. But there's an obvious gap: well-calibrated probabilities exist, they're just locked behind sportsbook spreadsheets or buried in academic papers."
          />
        </p>
        <p data-l="en">
          This project closes that gap with a transparent four-model ensemble — Dixon-Coles, a hierarchical Bayesian
          Poisson, gradient boosting, and Kalshi market features — stacked, isotonically calibrated, and propagated
          through {getMeta().n_sims.toLocaleString()} Monte Carlo bracket simulations.
        </p>
        <p data-l="es">
          Este proyecto cierra ese vacío con un ensamble transparente de cuatro modelos — Dixon-Coles, un Poisson
          bayesiano jerárquico, gradient boosting y features de mercado de Kalshi — apilados, calibrados
          isotónicamente y propagados a través de {getMeta().n_sims.toLocaleString()} simulaciones Monte Carlo del
          bracket.
        </p>
        <p data-l="en">
          Everything is reproducible. The repository ships the data fetchers, the model fits, the backtest harness
          with anti-leakage CI assertions, and a strategy layer that maximizes <em>expected pool points</em> (not
          argmax). Pool format and scoring rubric are configurable.
        </p>
        <p data-l="es">
          Todo es reproducible. El repositorio incluye los fetchers de datos, los ajustes de los modelos, el arnés
          de backtesting con aserciones de CI anti-fuga de información, y una capa de estrategia que maximiza los{" "}
          <em>puntos esperados de la quiniela</em> (no el argmax). El formato de la quiniela y la rúbrica de
          puntuación son configurables.
        </p>

        <h2 className="display text-2xl tracking-tight mt-10 text-[color:var(--color-ink)]">
          <L es="Autor" en="Author" />
        </h2>
        <p data-l="en">
          <strong className="text-[color:var(--color-ink)]">Daniel Regalado</strong>. MS Business Analytics, University of Miami.
          Bilingual ES/EN. Find me on{" "}
          <a className="text-[color:var(--color-red)] hover:underline" href="https://github.com/DanielRegaladoUMiami">GitHub</a>{" "}
          or read the{" "}
          <a className="text-[color:var(--color-red)] hover:underline" href="/methodology">methodology</a>.
        </p>
        <p data-l="es">
          <strong className="text-[color:var(--color-ink)]">Daniel Regalado</strong>. Maestría en Business Analytics, University of Miami.
          Bilingüe ES/EN. Encuéntrame en{" "}
          <a className="text-[color:var(--color-red)] hover:underline" href="https://github.com/DanielRegaladoUMiami">GitHub</a>{" "}
          o lee la{" "}
          <a className="text-[color:var(--color-red)] hover:underline" href="/methodology">metodología</a>.
        </p>

        <h2 className="display text-2xl tracking-tight mt-10 text-[color:var(--color-ink)]">
          <L es="Licencia y aviso legal" en="License & disclaimer" />
        </h2>
        <p className="text-[color:var(--color-ink-soft)] text-sm">
          <L
            es="Apache 2.0. El dashboard de Gradio vive en Hugging Face Spaces; el sitio estático que estás leyendo es el front-end de producción. Esto no es asesoría financiera. Todos los modelos están equivocados; algunos son útiles."
            en="Apache 2.0. The Gradio dashboard lives on Hugging Face Spaces; the static site you're reading is the production front-end. Not financial advice. Models are wrong; some are useful."
          />
        </p>
      </section>
    </div>
  );
}
