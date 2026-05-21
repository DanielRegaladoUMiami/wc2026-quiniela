"use client";
import { motion } from "framer-motion";

export default function ProbabilityBar({
  value,
  max = 1,
  color = "emerald",
  label,
  rightLabel,
  height = 8,
  delay = 0,
}: {
  value: number;
  max?: number;
  color?: "emerald" | "amber" | "sky" | "rose" | "slate";
  label?: string;
  rightLabel?: string;
  height?: number;
  delay?: number;
}) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100));
  const palette = {
    emerald: "from-emerald-400 to-emerald-600",
    amber: "from-amber-300 to-amber-500",
    sky: "from-sky-400 to-sky-600",
    rose: "from-rose-400 to-rose-600",
    slate: "from-slate-400 to-slate-600",
  }[color];

  return (
    <div className="w-full">
      {(label || rightLabel) && (
        <div className="flex justify-between text-xs text-slate-400 mb-1">
          <span>{label}</span>
          <span className="text-slate-200 tabular-nums">{rightLabel}</span>
        </div>
      )}
      <div
        className="relative overflow-hidden rounded-full bg-white/5 ring-1 ring-white/5"
        style={{ height }}
      >
        <motion.div
          className={`h-full rounded-full bg-gradient-to-r ${palette}`}
          initial={{ width: 0 }}
          whileInView={{ width: `${pct}%` }}
          viewport={{ once: true, margin: "-50px" }}
          transition={{ duration: 0.9, delay, ease: [0.16, 1, 0.3, 1] }}
        />
      </div>
    </div>
  );
}
