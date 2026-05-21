"use client";
import { BlockMath } from "react-katex";

export default function MathBlock({ children }: { children: string }) {
  return (
    <div className="my-3 px-4 py-3 rounded-lg bg-white/[0.03] border border-[color:var(--color-line)] overflow-x-auto">
      <BlockMath math={children} />
    </div>
  );
}
