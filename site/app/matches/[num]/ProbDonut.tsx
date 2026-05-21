"use client";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";

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
    { name: home, value: pH, fill: "#10b981" },
    { name: "Draw", value: pD, fill: "#64748b" },
    { name: away, value: pA, fill: "#fbbf24" },
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
            stroke="rgba(11,18,32,1)"
            strokeWidth={4}
            dataKey="value"
          >
            {data.map((d, i) => <Cell key={i} fill={d.fill} />)}
          </Pie>
          <Tooltip
            contentStyle={{ background: "#0b1220", border: "1px solid rgba(148,163,184,0.2)", borderRadius: 8, fontSize: 12 }}
            formatter={(v) => (typeof v === "number" ? `${(v * 100).toFixed(1)}%` : String(v))}
          />
        </PieChart>
      </ResponsiveContainer>
      <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
        <div className="text-xs text-slate-500">Most likely</div>
        <div className="font-display text-lg font-bold">
          {pH >= pD && pH >= pA ? home : pA >= pD ? away : "Draw"}
        </div>
      </div>
      <div className="flex gap-4 justify-center mt-2 text-xs">
        <Legend color="#10b981" label={home} val={pH} />
        <Legend color="#64748b" label="Draw" val={pD} />
        <Legend color="#fbbf24" label={away} val={pA} />
      </div>
    </div>
  );
}

function Legend({ color, label, val }: { color: string; label: string; val: number }) {
  return (
    <div className="flex items-center gap-1.5">
      <span className="h-2 w-2 rounded-full" style={{ background: color }} />
      <span className="text-slate-400">{label}</span>
      <span className="text-slate-200 tabular-nums">{(val * 100).toFixed(1)}%</span>
    </div>
  );
}
