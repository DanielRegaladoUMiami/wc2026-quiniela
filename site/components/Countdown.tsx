"use client";
import { useEffect, useState } from "react";

const TARGET = new Date("2026-06-11T17:00:00-05:00").getTime();

function compute(): { d: number; h: number; m: number; s: number; live: boolean } {
  const diff = TARGET - Date.now();
  if (diff <= 0) return { d: 0, h: 0, m: 0, s: 0, live: true };
  const d = Math.floor(diff / 86400000);
  const h = Math.floor((diff % 86400000) / 3600000);
  const m = Math.floor((diff % 3600000) / 60000);
  const s = Math.floor((diff % 60000) / 1000);
  return { d, h, m, s, live: false };
}

const Cell = ({ n, label }: { n: number; label: string }) => (
  <div className="flex flex-col items-center">
    <div className="display text-3xl sm:text-5xl tabular-nums text-[color:var(--color-ink)]">
      {n.toString().padStart(2, "0")}
    </div>
    <div className="display text-[10px] sm:text-xs tracking-[0.2em] text-[color:var(--color-ink-soft)] mt-1">
      {label}
    </div>
  </div>
);

export default function Countdown() {
  const [t, setT] = useState(compute);
  useEffect(() => {
    const id = setInterval(() => setT(compute()), 1000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="sticker inline-flex items-center gap-4 sm:gap-6 rounded-none px-5 py-4">
      <Cell n={t.d} label="Days" />
      <div className="display text-2xl text-[color:var(--color-red)]">:</div>
      <Cell n={t.h} label="Hours" />
      <div className="display text-2xl text-[color:var(--color-red)]">:</div>
      <Cell n={t.m} label="Min" />
      <div className="display text-2xl text-[color:var(--color-red)]">:</div>
      <Cell n={t.s} label="Sec" />
    </div>
  );
}
