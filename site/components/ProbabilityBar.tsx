// Pure-CSS animated probability bar. Server-renderable, zero client JS.
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
  const fill = {
    emerald: "var(--color-blue)",
    amber: "var(--color-yellow)",
    sky: "var(--color-blue)",
    rose: "var(--color-red)",
    slate: "var(--color-ink-soft)",
  }[color];

  return (
    <div className="w-full">
      {(label || rightLabel) && (
        <div className="flex justify-between text-xs text-[color:var(--color-ink-soft)] mb-1">
          <span>{label}</span>
          <span className="text-[color:var(--color-ink)] tabular-nums">{rightLabel}</span>
        </div>
      )}
      <div
        className="relative overflow-hidden border-2 border-[color:var(--color-ink)] bar-track"
        style={{ height }}
      >
        <div
          className="h-full pb-anim"
          style={{
            width: `${pct}%`,
            backgroundColor: fill,
            animationDelay: `${delay}s`,
          }}
        />
      </div>
      <style>{`
        @keyframes pb-grow { from { transform: scaleX(0); } to { transform: scaleX(1); } }
        .pb-anim { transform-origin: left center; animation: pb-grow 0.9s cubic-bezier(0.16, 1, 0.3, 1) both; }
      `}</style>
    </div>
  );
}
