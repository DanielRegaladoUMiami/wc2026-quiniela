"use client";
import { Advancement, Team, fmtPct } from "@/lib/types";

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
      {/* headers */}
      {ROUNDS.map((r, i) => (
        <text
          key={r.key}
          x={labelW + i * colW + colW / 2}
          y={20}
          textAnchor="middle"
          fill="#6e5f3c"
          fontSize={11}
          fontFamily="var(--font-display)"
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
            <text x={0} y={y + 14} fontSize={13} fontWeight={600} fill="#211a0e" fontFamily="var(--font-display)">
              {a.team}
            </text>
            <text x={0} y={y + 28} fontSize={10} fill="#6e5f3c">
              {t?.fifa_code} · #{t?.fifa_rank}
            </text>

            {/* Bars per round */}
            {ROUNDS.map((r, i) => {
              const v = a[r.key] as number;
              const cx = labelW + i * colW;
              const barW = Math.max(2, v * (colW - 20));
              return (
                <g key={r.key}>
                  <rect x={cx} y={y + 6} width={colW - 20} height={24} fill="rgba(33,26,14,0.1)" stroke="#211a0e" strokeWidth={2} />
                  <rect x={cx} y={y + 6} width={barW} height={24} fill="#225fa0" stroke="#211a0e" strokeWidth={2} />
                  <text
                    x={cx + 6}
                    y={y + 21}
                    fontSize={10}
                    fill="#fbf5e6"
                    fontFamily="var(--font-mono)"
                    fontWeight={500}
                  >
                    {fmtPct(v, 0)}
                  </text>
                </g>
              );
            })}

            {/* Champion badge */}
            <g transform={`translate(${labelW + ROUNDS.length * colW + 10}, ${y + 6})`}>
              <rect width={60} height={24} fill="#efb22f" stroke="#211a0e" strokeWidth={2} />
              <text x={30} y={16} textAnchor="middle" fontSize={11} fill="#211a0e" fontFamily="var(--font-mono)" fontWeight={600}>
                {fmtPct(a.p_champion, 1)}
              </text>
            </g>
          </g>
        );
      })}

      <text x={labelW + ROUNDS.length * colW + 40} y={20} textAnchor="middle" fontSize={11} fill="#d63a2a" letterSpacing={2} fontFamily="var(--font-display)">
        CHAMPION
      </text>
    </svg>
  );
}
