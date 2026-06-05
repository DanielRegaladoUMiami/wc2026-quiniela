"use client";

function poissonPmf(k: number, lambda: number): number {
  if (lambda <= 0) return k === 0 ? 1 : 0;
  let logP = -lambda + k * Math.log(lambda);
  for (let i = 2; i <= k; i++) logP -= Math.log(i);
  return Math.exp(logP);
}

const MAX = 6;

// amber -> red ink ramp on cream (Panini heatmap)
function heatColor(t: number): string {
  // t in [0,1]: cream -> yellow -> red
  const cream = [251, 245, 230];
  const yellow = [239, 178, 47];
  const red = [214, 58, 42];
  let from: number[], to: number[], f: number;
  if (t < 0.5) {
    from = cream; to = yellow; f = t / 0.5;
  } else {
    from = yellow; to = red; f = (t - 0.5) / 0.5;
  }
  const c = from.map((v, i) => Math.round(v + (to[i] - v) * f));
  return `rgb(${c[0]}, ${c[1]}, ${c[2]})`;
}

export default function ScoreHeatmap({ lambdaH, lambdaA }: { lambdaH: number; lambdaA: number }) {
  const lH = Math.min(Math.max(lambdaH, 0.3), 5);
  const lA = Math.min(Math.max(lambdaA, 0.3), 5);

  // Build matrix; row = home goals, col = away goals
  const grid: { p: number; h: number; a: number }[][] = [];
  let max = 0;
  let argmax = { h: 0, a: 0 };
  for (let h = 0; h <= MAX; h++) {
    const row: { p: number; h: number; a: number }[] = [];
    for (let a = 0; a <= MAX; a++) {
      const p = poissonPmf(h, lH) * poissonPmf(a, lA);
      if (p > max) { max = p; argmax = { h, a }; }
      row.push({ p, h, a });
    }
    grid.push(row);
  }

  return (
    <div className="overflow-x-auto">
      <div className="inline-block">
        <div className="flex">
          <div className="w-6" />
          {Array.from({ length: MAX + 1 }, (_, i) => (
            <div key={i} className="w-9 text-center text-[10px] text-[color:var(--color-ink-soft)]">{i}</div>
          ))}
        </div>
        {grid.map((row, h) => (
          <div key={h} className="flex">
            <div className="w-6 text-right pr-1 text-[10px] text-[color:var(--color-ink-soft)] self-center">{h}</div>
            {row.map((cell) => {
              const intensity = cell.p / max;
              const isPeak = cell.h === argmax.h && cell.a === argmax.a;
              return (
                <div
                  key={cell.a}
                  className={`w-9 h-9 m-[1px] rounded-none border-2 border-[color:var(--color-ink)] text-[10px] flex items-center justify-center tabular-nums font-medium transition-transform hover:scale-110 ${isPeak ? "ring-2 ring-[color:var(--color-ink)]" : ""}`}
                  style={{
                    background: heatColor(intensity),
                    color: "#211a0e",
                  }}
                  title={`${cell.h}-${cell.a}: ${(cell.p * 100).toFixed(2)}%`}
                >
                  {(cell.p * 100).toFixed(0)}
                </div>
              );
            })}
          </div>
        ))}
        <div className="flex mt-2 text-[10px] text-[color:var(--color-ink-soft)]">
          <div className="w-6" />
          <div className="flex-1 text-center">Away goals →</div>
        </div>
      </div>
      <div className="text-xs text-[color:var(--color-ink-soft)] mt-3">
        Modal scoreline: <span className="text-[color:var(--color-red)] font-semibold tabular-nums">{argmax.h}–{argmax.a}</span>
        <span className="text-[color:var(--color-ink-soft)] mx-2">·</span>
        <span>{(max * 100).toFixed(2)}% mass</span>
      </div>
      <div className="text-[10px] text-[color:var(--color-ink-soft)] mt-1">
        Independent-Poisson approximation (λ<sub>home</sub> × λ<sub>away</sub>). The correlated
        Dixon-Coles / Monte-Carlo joint is served on match pages in the live build.
      </div>
    </div>
  );
}
