import { confColor } from "@/lib/utils";

export default function ConfederationChip({ conf, size = "sm" }: { conf: string; size?: "xs" | "sm" }) {
  const cls = confColor(conf);
  const text = size === "xs" ? "text-[10px] px-1.5 py-0.5" : "text-xs px-2 py-0.5";
  return (
    <span className={`display inline-flex items-center rounded-none border-2 leading-none ${cls} ${text}`}>
      {conf}
    </span>
  );
}
