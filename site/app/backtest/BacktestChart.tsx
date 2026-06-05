"use client";
import { BacktestRow } from "@/lib/types";
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
          <CartesianGrid stroke="rgba(33,26,14,0.12)" />
          <XAxis dataKey="i" tick={{ fill: "#6e5f3c", fontSize: 11 }} axisLine={{ stroke: "rgba(33,26,14,0.4)" }} />
          <YAxis tick={{ fill: "#6e5f3c", fontSize: 11 }} axisLine={{ stroke: "rgba(33,26,14,0.4)" }} domain={["auto", "auto"]} />
          <Tooltip
            contentStyle={{ background: "#fbf5e6", border: "2px solid #211a0e", borderRadius: 0, fontSize: 12, color: "#211a0e" }}
            formatter={(v) => (typeof v === "number" ? v.toFixed(3) : String(v))}
            labelFormatter={(l) => `Match ${l}`}
          />
          <ReferenceLine y={1.0986} stroke="#efb22f" strokeWidth={2} strokeDasharray="3 3" label={{ value: "Uniform (log 3)", fill: "#211a0e", fontSize: 10 }} />
          <Line type="monotone" dataKey="avg" stroke="#225fa0" strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
