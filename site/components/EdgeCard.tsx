import FlagImg from "@/components/FlagImg";
import type { EdgeMatch } from "@/lib/types";

const pct = (x: number) => Math.round(x * 100);

export default function EdgeCard({ m, rank }: { m: EdgeMatch; rank: number }) {
  const leanCode =
    m.best_edge_side === "draw" ? "DRAW" : m.best_edge_side === "home" ? m.home_code : m.away_code;
  const date = new Date(m.date)
    .toLocaleDateString("en-US", { month: "short", day: "2-digit" })
    .toUpperCase();

  const rows = [
    { k: "home", label: m.home_team, model: m.p_home_model, mkt: m.p_home_market },
    { k: "draw", label: "Draw", model: m.p_draw_model, mkt: m.p_draw_market },
    { k: "away", label: m.away_team, model: m.p_away_model, mkt: m.p_away_market },
  ];

  return (
    <div className="sticker sticker-hover">
      <div className="halftone flex items-center justify-between gap-2 border-b-2 border-[color:var(--color-ink)] bg-[color:var(--color-blue)] px-3 py-1.5 text-[color:var(--color-card)]">
        <span className="display text-sm leading-none">
          #{String(rank).padStart(2, "0")} · {date}
        </span>
        <span className="stamp px-2 py-0.5 text-[11px] leading-none">
          ▲ {leanCode} +{m.best_edge_pts.toFixed(0)}
        </span>
      </div>

      <div className="p-4">
        <div className="mb-4 flex items-center justify-center gap-4">
          <div className="flex flex-col items-center gap-1.5">
            <FlagImg iso2={m.home_iso2} size={44} className="!rounded-none border-2 border-[color:var(--color-ink)] !ring-0" />
            <span className="display text-2xl leading-none">{m.home_code}</span>
          </div>
          <span className="display text-lg text-[color:var(--color-red)]">VS</span>
          <div className="flex flex-col items-center gap-1.5">
            <FlagImg iso2={m.away_iso2} size={44} className="!rounded-none border-2 border-[color:var(--color-ink)] !ring-0" />
            <span className="display text-2xl leading-none">{m.away_code}</span>
          </div>
        </div>

        <div className="space-y-2">
          {rows.map((r) => {
            const isLean = r.k === m.best_edge_side;
            return (
              <div key={r.k} className={isLean ? "-mx-1 bg-[color:var(--color-yellow)]/35 px-1 py-0.5" : ""}>
                <div className="mb-1 flex items-center justify-between text-[12px]">
                  <span className="display text-sm leading-none">{r.label}</span>
                  <span className="font-mono tabular-nums">
                    <span className="font-bold text-[color:var(--color-blue)]">{pct(r.model)}%</span>
                    <span className="text-[color:var(--color-ink-soft)]"> / {pct(r.mkt)}%</span>
                  </span>
                </div>
                <div className="relative h-3 border-2 border-[color:var(--color-ink)] bar-track">
                  <div
                    className="absolute inset-y-0 left-0 bg-[color:var(--color-blue)]"
                    style={{ width: `${pct(r.model)}%` }}
                  />
                  <div
                    className="absolute inset-y-[-3px] w-[3px] bg-[color:var(--color-red)] border-x border-[color:var(--color-ink)]"
                    style={{ left: `${pct(r.mkt)}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>

        <div className="mt-3 flex items-center gap-4 border-t-2 border-dotted border-[color:var(--color-line-soft)] pt-2 text-[10px] text-[color:var(--color-ink-soft)]">
          <span className="flex items-center gap-1">
            <span className="inline-block h-2 w-3 bg-[color:var(--color-blue)] border border-[color:var(--color-ink)]" /> model
          </span>
          <span className="flex items-center gap-1">
            <span className="inline-block h-2.5 w-[3px] bg-[color:var(--color-red)]" /> the line
          </span>
        </div>
      </div>
    </div>
  );
}
