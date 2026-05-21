"use client";
import { Advancement, Team, fmtPct } from "@/lib/data";

// Renders a clean horizontal funnel of P(reach round) for the top N teams.
// Rounds: R32 → R16 → QF → SF → Final → Champion
const ROUNDS: { key: keyof Advancement; label: string }[] = [
  { key: "p_R32_win", label: "R16" },
  { key: "p_R16_win", label: "QF" },
  { key: "p_QF_win", label: "SF" },
  { key: "p_SF_win", label: "Final" },
  { key: "p_final_win", label: "Champ" },
];

export default function BracketSVG({ advancement, teams }: { advancement: Advancement[]; teams: Team[] }) {
  const teamMap = new Map(teams.map((t) => [t.team, t]));
  const rowH = 38;
  const labelW = 180;
  const colW = 130;
  const w = labelW + ROUNDS.length * colW + 80;
  const h = advancement.length * rowH + 60;

  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="w-full min-w-[820px]">
      <defs>
        <linearGradient id="barGrad" x1="0" x2="1">
          <stop offset="0%" stopColor="#10b981" />
          <stop offset="100%" stopColor="#fbbf24" />
        </linearGradient>
      </defs>
      {/* headers */}
      {ROUNDS.map((r, i) => (
        <text
          key={r.key}
          x={labelW + i * colW + colW / 2}
          y={20}
          textAnchor="middle"
          className="fill-slate-400"
          fontSize={11}
          fontFamily="var(--font-space-grotesk)"
          letterSpacing={2}
        >
          {r.label.toUpperCase()}
        </text>
      ))}

      {advancement.map((a, idx) => {
        const t = teamMap.get(a.team);
        const y = 40 + idx * rowH;
        return (
          <g key={a.team}>
            {/* Team label */}
            <text x={0} y={y + 14} fontSize={13} fontWeight={600} className="fill-slate-100" fontFamily="var(--font-space-grotesk)">
              {a.team}
            </text>
            <text x={0} y={y + 28} fontSize={10} className="fill-slate-500">
              {t?.fifa_code} · #{t?.fifa_rank}
            </text>

            {/* Bars per round */}
            {ROUNDS.map((r, i) => {
              const v = a[r.key] as number;
              const cx = labelW + i * colW;
              const barW = Math.max(2, v * (colW - 20));
              return (
                <g key={r.key}>
                  <rect x={cx} y={y + 6} width={colW - 20} height={24} rx={4} fill="rgba(255,255,255,0.04)" />
                  <rect x={cx} y={y + 6} width={barW} height={24} rx={4} fill="url(#barGrad)" opacity={0.85} />
                  <text
                    x={cx + 6}
                    y={y + 21}
                    fontSize={10}
                    className="fill-slate-100"
                    fontFamily="ui-monospace, monospace"
                    fontWeight={500}
                  >
                    {fmtPct(v, 0)}
                  </text>
                </g>
              );
            })}

            {/* Champion badge */}
            <g transform={`translate(${labelW + ROUNDS.length * colW + 10}, ${y + 6})`}>
              <rect width={60} height={24} rx={4} fill="rgba(251,191,36,0.12)" stroke="rgba(251,191,36,0.3)" />
              <text x={30} y={16} textAnchor="middle" fontSize={11} className="fill-amber-300" fontFamily="ui-monospace, monospace" fontWeight={600}>
                {fmtPct(a.p_champion, 1)}
              </text>
            </g>
          </g>
        );
      })}

      <text x={labelW + ROUNDS.length * colW + 40} y={20} textAnchor="middle" fontSize={11} className="fill-amber-300" letterSpacing={2} fontFamily="var(--font-space-grotesk)">
        CHAMPION
      </text>
    </svg>
  );
}
