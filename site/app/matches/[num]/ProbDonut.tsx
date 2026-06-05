"use client";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";
import L from "@/components/L";

export default function ProbDonut({
  pH,
  pD,
  pA,
  home,
  away,
}: {
  pH: number;
  pD: number;
  pA: number;
  home: string;
  away: string;
}) {
  const data = [
    { name: home, value: pH, fill: "#225fa0" },
    { name: "Draw", value: pD, fill: "#6e5f3c" },
    { name: away, value: pA, fill: "#efb22f" },
  ];
  return (
    <div className="h-64 relative">
      <ResponsiveContainer>
        <PieChart>
          <Pie
            data={data}
            innerRadius={70}
            outerRadius={100}
            startAngle={90}
            endAngle={-270}
            stroke="#211a0e"
            strokeWidth={4}
            dataKey="value"
          >
            {data.map((d, i) => <Cell key={i} fill={d.fill} />)}
          </Pie>
          <Tooltip
            contentStyle={{ background: "#fbf5e6", border: "2px solid #211a0e", borderRadius: 0, fontSize: 12, color: "#211a0e" }}
            formatter={(v) => (typeof v === "number" ? `${(v * 100).toFixed(1)}%` : String(v))}
          />
        </PieChart>
      </ResponsiveContainer>
      <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
        <div className="text-xs text-[color:var(--color-ink-soft)]">
          <L es="Más probable" en="Most likely" />
        </div>
        <div className="display text-lg">
          {pH >= pD && pH >= pA ? home : pA >= pD ? away : "Draw"}
        </div>
      </div>
      <div className="flex gap-4 justify-center mt-2 text-xs">
        <Legend color="#225fa0" label={home} val={pH} />
        <Legend color="#6e5f3c" label="Draw" val={pD} />
        <Legend color="#efb22f" label={away} val={pA} />
      </div>
    </div>
  );
}

function Legend({ color, label, val }: { color: string; label: string; val: number }) {
  return (
    <div className="flex items-center gap-1.5">
      <span className="h-2 w-2 border border-[color:var(--color-ink)]" style={{ background: color }} />
      <span className="text-[color:var(--color-ink-soft)]">{label}</span>
      <span className="text-[color:var(--color-ink)] tabular-nums">{(val * 100).toFixed(1)}%</span>
    </div>
  );
}
