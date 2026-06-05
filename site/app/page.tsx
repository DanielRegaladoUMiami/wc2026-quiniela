import EdgeCard from "@/components/EdgeCard";
import { getEdge } from "@/lib/data";

export default function Page() {
  const edges = [...getEdge()].sort((a, b) => b.best_edge_pts - a.best_edge_pts);
  const avg = edges.reduce((s, m) => s + m.best_edge_pts, 0) / (edges.length || 1);
  const strong = edges.filter((m) => m.best_edge_pts >= 8).length;

  return (
    <div className="mx-auto max-w-screen-2xl px-4 sm:px-6 py-8">
      {/* album-cover header */}
      <div className="sticker mb-9 overflow-hidden">
        <div className="halftone border-b-2 border-[color:var(--color-ink)] bg-[color:var(--color-red)] px-5 py-2">
          <span className="display text-sm text-[color:var(--color-card)]">
            OFFICIAL ALBUM · WC 2026 · WHERE WE BEAT THE HOUSE
          </span>
        </div>
        <div className="p-5 sm:p-8">
          <h1 className="display text-6xl sm:text-8xl leading-[0.82] text-[color:var(--color-ink)]">
            THE <span className="text-[color:var(--color-red)]">EDGE</span>
          </h1>
          <p className="mt-4 max-w-2xl text-sm leading-relaxed text-[color:var(--color-ink-soft)]">
            Our model&apos;s win probability against the de-vigged{" "}
            <span className="font-bold text-[color:var(--color-ink)]">DraftKings</span> closing line,
            for every World Cup group-stage match. The blue bar is us; the red tick is the market.
            The wider they split, the more we disagree. The{" "}
            <span className="font-bold text-[color:var(--color-ink)]">closing-line value</span> decides
            who&apos;s right — live, during the tournament. We show it, we don&apos;t claim it.
          </p>
          <div className="mt-6 flex flex-wrap gap-x-8 gap-y-3">
            <Stat v={edges.length} k="MATCHES" color="var(--color-blue)" />
            <Stat v={strong} k="GAPS ≥ 8 PTS" color="var(--color-red)" />
            <Stat v={avg.toFixed(1)} k="AVG GAP" color="var(--color-green)" />
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

function Stat({ v, k, color }: { v: number | string; k: string; color: string }) {
  return (
    <div className="flex items-baseline gap-2">
      <span className="display text-4xl tabular-nums" style={{ color }}>
        {v}
      </span>
      <span className="text-[11px] font-semibold tracking-wide text-[color:var(--color-ink-soft)]">
        {k}
      </span>
    </div>
  );
}
