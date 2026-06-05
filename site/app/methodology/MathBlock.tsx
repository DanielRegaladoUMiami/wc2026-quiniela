"use client";
import { BlockMath } from "react-katex";

export default function MathBlock({ children }: { children: string }) {
  return (
    <div className="sticker my-3 rounded-none px-4 py-3 text-[color:var(--color-ink)] overflow-x-auto">
      <BlockMath math={children} />
    </div>
  );
}
