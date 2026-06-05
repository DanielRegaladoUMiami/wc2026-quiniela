import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const CONFEDERATIONS = ["UEFA", "CONMEBOL", "CONCACAF", "CAF", "AFC", "OFC"] as const;

export function confColor(conf: string): string {
  switch (conf) {
    case "UEFA": return "text-[color:var(--color-card)] bg-[color:var(--color-blue)] border-[color:var(--color-ink)]";
    case "CONMEBOL": return "text-[color:var(--color-ink)] bg-[color:var(--color-yellow)] border-[color:var(--color-ink)]";
    case "CONCACAF": return "text-[color:var(--color-card)] bg-[color:var(--color-green)] border-[color:var(--color-ink)]";
    case "CAF": return "text-[color:var(--color-card)] bg-[color:var(--color-red)] border-[color:var(--color-ink)]";
    case "AFC": return "text-[color:var(--color-card)] bg-[color:var(--color-ink)] border-[color:var(--color-ink)]";
    case "OFC": return "text-[color:var(--color-ink)] bg-[color:var(--color-card)] border-[color:var(--color-ink)]";
    default: return "text-[color:var(--color-ink)] bg-[color:var(--color-card)] border-[color:var(--color-ink)]";
  }
}

export function fmtDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" });
}
