import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const CONFEDERATIONS = ["UEFA", "CONMEBOL", "CONCACAF", "CAF", "AFC", "OFC"] as const;

export function confColor(conf: string): string {
  switch (conf) {
    case "UEFA": return "text-sky-300 bg-sky-500/10 border-sky-500/30";
    case "CONMEBOL": return "text-yellow-300 bg-yellow-500/10 border-yellow-500/30";
    case "CONCACAF": return "text-emerald-300 bg-emerald-500/10 border-emerald-500/30";
    case "CAF": return "text-orange-300 bg-orange-500/10 border-orange-500/30";
    case "AFC": return "text-red-300 bg-red-500/10 border-red-500/30";
    case "OFC": return "text-violet-300 bg-violet-500/10 border-violet-500/30";
    default: return "text-slate-300 bg-slate-500/10 border-slate-500/30";
  }
}

export function fmtDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" });
}
