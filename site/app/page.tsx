import EdgeCard from "@/components/EdgeCard";
import L from "@/components/L";
import { getEdge } from "@/lib/data";

export default function Page() {
  const edges = [...getEdge()].sort((a, b) => b.best_edge_pts - a.best_edge_pts);
  const avg = edges.reduce((s, m) => s + m.best_edge_pts, 0) / (edges.length || 1);
  const strong = edges.filter((m) => m.best_edge_pts >= 8).length;

  return (
    <div className="mx-auto max-w-screen-2xl px-4 sm:px-6 py-8">
      <div className="sticker mb-9 overflow-hidden">
        <div className="halftone border-b-2 border-[color:var(--color-ink)] bg-[color:var(--color-red)] px-5 py-2">
          <span className="display text-sm text-[color:var(--color-card)]">
            <L
              es="ÁLBUM OFICIAL · WC 2026 · DONDE LE GANAMOS A LA CASA"
              en="OFFICIAL ALBUM · WC 2026 · WHERE WE BEAT THE HOUSE"
            />
          </span>
        </div>
        <div className="p-5 sm:p-8">
          <h1 className="display text-6xl sm:text-8xl leading-[0.82] text-[color:var(--color-ink)]">
            <L es="EL " en="THE " />
            <span className="text-[color:var(--color-red)]">EDGE</span>
          </h1>
          <p
            data-l="en"
            className="mt-4 max-w-2xl text-sm leading-relaxed text-[color:var(--color-ink-soft)]"
          >
            Our model&apos;s win probability against the de-vigged{" "}
            <span className="font-bold text-[color:var(--color-ink)]">DraftKings</span> closing line,
            for every World Cup group-stage match. The blue bar is us; the red tick is the market.
            The wider they split, the more we disagree. The{" "}
            <span className="font-bold text-[color:var(--color-ink)]">closing-line value</span>{" "}
            decides who&apos;s right — live, during the tournament. We show it, we don&apos;t claim it.
          </p>
          <p
            data-l="es"
            className="mt-4 max-w-2xl text-sm leading-relaxed text-[color:var(--color-ink-soft)]"
          >
            La probabilidad de nuestro modelo contra la línea de cierre de{" "}
            <span className="font-bold text-[color:var(--color-ink)]">DraftKings</span> (sin la
            comisión de la casa), en cada partido de fase de grupos. La barra azul somos nosotros; la
            marca roja es el mercado. Mientras más se separan, más diferimos. El{" "}
            <span className="font-bold text-[color:var(--color-ink)]">closing-line value</span> decide
            quién tiene razón — en vivo, durante el Mundial. Lo mostramos, no lo presumimos.
          </p>
          <div className="mt-6 flex flex-wrap gap-x-8 gap-y-3">
            <Stat v={edges.length} es="PARTIDOS" en="MATCHES" color="var(--color-blue)" />
            <Stat v={strong} es="BRECHAS ≥ 8 PTS" en="GAPS ≥ 8 PTS" color="var(--color-red)" />
            <Stat v={avg.toFixed(1)} es="BRECHA PROM." en="AVG GAP" color="var(--color-green)" />
          </div>
        </div>
      </div>

      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4">
        {edges.map((m, i) => (
          <EdgeCard key={`${m.home_team}-${m.away_team}`} m={m} rank={i + 1} />
        ))}
      </div>
    </div>
  );
}

function Stat({
  v,
  es,
  en,
  color,
}: {
  v: number | string;
  es: string;
  en: string;
  color: string;
}) {
  return (
    <div className="flex items-baseline gap-2">
      <span className="display text-4xl tabular-nums" style={{ color }}>
        {v}
      </span>
      <span className="text-[11px] font-semibold tracking-wide text-[color:var(--color-ink-soft)]">
        <L es={es} en={en} />
      </span>
    </div>
  );
}
