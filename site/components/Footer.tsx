import L from "@/components/L";
import { getMeta } from "@/lib/data";

export default function Footer() {
  const meta = getMeta();
  const stamp = meta.generated_at.slice(0, 10);
  return (
    <footer className="mt-12 border-t-2 border-[color:var(--color-ink)] bg-[color:var(--color-paper-deep)]">
      <div className="mx-auto flex max-w-screen-2xl flex-wrap items-center gap-x-5 gap-y-1 px-4 py-3 text-[11px] font-semibold text-[color:var(--color-ink-soft)] sm:px-6">
        <span className="display text-sm text-[color:var(--color-ink)]">WC26 QUINIELA</span>
        <span>·</span>
        <span>SIM {meta.sim_run}</span>
        <span>
          {meta.n_sims.toLocaleString()} sims · {meta.n_matches}{" "}
          <L es="partidos" en="matches" />
        </span>
        <span data-l="en">
          RPS <span className="text-[color:var(--color-red)]">≈0.20</span> walk-forward · leakage-free
        </span>
        <span data-l="es">
          RPS <span className="text-[color:var(--color-red)]">≈0.20</span> walk-forward · sin fugas
        </span>
        <span>
          <L es="ACTUALIZADO" en="UPDATED" /> {stamp}
        </span>
        <span className="ml-auto flex items-center gap-4">
          <a className="hover:text-[color:var(--color-red)]" href="https://github.com/DanielRegaladoUMiami/wc2026-quiniela">
            GITHUB
          </a>
          <a className="hover:text-[color:var(--color-red)]" href="/methodology">
            <L es="MÉTODO" en="METHOD" />
          </a>
        </span>
      </div>
      <div className="mx-auto max-w-screen-2xl px-4 pb-3 text-[10px] text-[color:var(--color-ink-soft)] opacity-80 sm:px-6">
        <L
          es="esto no es asesoría financiera · todos los modelos se equivocan, algunos sirven · Apache 2.0"
          en="not financial advice · models are wrong, some are useful · Apache 2.0"
        />
      </div>
    </footer>
  );
}
