"use client";
import { BacktestRow } from "@/lib/data";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, ReferenceLine } from "recharts";

export default function BacktestChart({ wc, eu }: { wc: BacktestRow[]; eu: BacktestRow[] }) {
  const all = [...wc.map((r) => ({ ...r, tour: "WC22" })), ...eu.map((r) => ({ ...r, tour: "EU24" }))].sort(
    (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime(),
  );
  const probs = ["p_home", "p_draw", "p_away"] as const;
  let cum = 0;
  const data = all.map((r, i) => {
    const p = Math.max(1e-9, r[probs[r.outcome]] ?? 1e-9);
    cum -= Math.log(p);
    return { i: i + 1, tour: r.tour, avg: cum / (i + 1), date: r.date };
  });

  return (
    <div className="h-64">
      <ResponsiveContainer>
        <LineChart data={data} margin={{ top: 5, right: 16, left: 0, bottom: 0 }}>
          <CartesianGrid stroke="rgba(148,163,184,0.08)" />
          <XAxis dataKey="i" tick={{ fill: "#64748b", fontSize: 11 }} axisLine={{ stroke: "rgba(148,163,184,0.2)" }} />
          <YAxis tick={{ fill: "#64748b", fontSize: 11 }} axisLine={{ stroke: "rgba(148,163,184,0.2)" }} domain={["auto", "auto"]} />
          <Tooltip
            contentStyle={{ background: "#0b1220", border: "1px solid rgba(148,163,184,0.2)", borderRadius: 8, fontSize: 12 }}
            formatter={(v: number) => v.toFixed(3)}
            labelFormatter={(l) => `Match ${l}`}
          />
          <ReferenceLine y={1.0986} stroke="#fbbf24" strokeDasharray="3 3" label={{ value: "Uniform (log 3)", fill: "#fbbf24", fontSize: 10 }} />
          <Line type="monotone" dataKey="avg" stroke="#10b981" strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
