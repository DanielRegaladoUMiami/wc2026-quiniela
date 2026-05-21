"use client";
import { useMemo, useState } from "react";
import TeamCard from "@/components/TeamCard";
import { Team } from "@/lib/types";
import { CONFEDERATIONS } from "@/lib/utils";

type SortKey = "champion" | "advance" | "rank" | "name";

export default function TeamsExplorer({ teams }: { teams: Team[] }) {
  const [conf, setConf] = useState<string | null>(null);
  const [sort, setSort] = useState<SortKey>("champion");
  const [q, setQ] = useState("");

  const filtered = useMemo(() => {
    let arr = teams.slice();
    if (conf) arr = arr.filter((t) => t.conf === conf);
    if (q) {
      const qq = q.toLowerCase();
      arr = arr.filter(
        (t) => t.team.toLowerCase().includes(qq) || t.nickname?.toLowerCase().includes(qq),
      );
    }
    arr.sort((a, b) => {
      switch (sort) {
        case "champion": return (b.p_champion ?? 0) - (a.p_champion ?? 0);
        case "advance": return (b.p_advance_group ?? 0) - (a.p_advance_group ?? 0);
        case "rank": return a.fifa_rank - b.fifa_rank;
        case "name": return a.team.localeCompare(b.team);
      }
    });
    return arr;
  }, [teams, conf, sort, q]);

  return (
    <div>
      <div className="flex flex-wrap gap-2 items-center mb-6">
        <button
          onClick={() => setConf(null)}
          className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
            conf === null ? "bg-white/10 border-white/20 text-white" : "border-[color:var(--color-line)] text-slate-400 hover:text-white hover:border-white/20"
          }`}
        >
          All ({teams.length})
        </button>
        {CONFEDERATIONS.map((c) => {
          const n = teams.filter((t) => t.conf === c).length;
          if (!n) return null;
          return (
            <button
              key={c}
              onClick={() => setConf(c === conf ? null : c)}
              className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
                conf === c ? "bg-emerald-500/10 border-emerald-500/40 text-emerald-300" : "border-[color:var(--color-line)] text-slate-400 hover:text-white hover:border-white/20"
              }`}
            >
              {c} ({n})
            </button>
          );
        })}
        <div className="ml-auto flex items-center gap-2">
          <input
            placeholder="Search teams..."
            value={q}
            onChange={(e) => setQ(e.target.value)}
            className="bg-white/5 border border-[color:var(--color-line)] rounded-md px-3 py-1.5 text-sm w-44 focus:outline-none focus:border-emerald-500/40"
          />
          <select
            value={sort}
            onChange={(e) => setSort(e.target.value as SortKey)}
            className="bg-white/5 border border-[color:var(--color-line)] rounded-md px-3 py-1.5 text-sm focus:outline-none"
          >
            <option value="champion">Sort: Champion %</option>
            <option value="advance">Sort: Advance %</option>
            <option value="rank">Sort: FIFA rank</option>
            <option value="name">Sort: Name</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {filtered.map((t, i) => (
          <TeamCard key={t.fifa_code} team={t} priority={i < 8} />
        ))}
      </div>
      {filtered.length === 0 && (
        <div className="text-center text-slate-500 py-20">No teams match those filters.</div>
      )}
    </div>
  );
}
