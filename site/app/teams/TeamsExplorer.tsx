"use client";
import { useMemo, useState } from "react";
import L from "@/components/L";
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
          className={`display text-sm px-3 py-1.5 rounded-none border-2 border-[color:var(--color-ink)] transition-colors ${
            conf === null
              ? "bg-[color:var(--color-ink)] text-[color:var(--color-yellow)]"
              : "bg-[color:var(--color-yellow)] text-[color:var(--color-ink)] hover:bg-[color:var(--color-ink)] hover:text-[color:var(--color-yellow)]"
          }`}
        >
          <L es="TODOS" en="ALL" /> ({teams.length})
        </button>
        {CONFEDERATIONS.map((c) => {
          const n = teams.filter((t) => t.conf === c).length;
          if (!n) return null;
          return (
            <button
              key={c}
              onClick={() => setConf(c === conf ? null : c)}
              className={`display text-sm px-3 py-1.5 rounded-none border-2 border-[color:var(--color-ink)] transition-colors ${
                conf === c
                  ? "bg-[color:var(--color-ink)] text-[color:var(--color-yellow)]"
                  : "bg-[color:var(--color-yellow)] text-[color:var(--color-ink)] hover:bg-[color:var(--color-ink)] hover:text-[color:var(--color-yellow)]"
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
            className="bg-[color:var(--color-card)] border-2 border-[color:var(--color-ink)] rounded-none px-3 py-1.5 text-sm w-44 text-[color:var(--color-ink)] placeholder:text-[color:var(--color-ink-soft)] focus:outline-none focus:border-[color:var(--color-red)]"
          />
          <select
            value={sort}
            onChange={(e) => setSort(e.target.value as SortKey)}
            className="display bg-[color:var(--color-card)] border-2 border-[color:var(--color-ink)] rounded-none px-3 py-1.5 text-sm text-[color:var(--color-ink)] focus:outline-none focus:border-[color:var(--color-red)]"
          >
            <option value="champion">Sort: Champion %</option>
            <option value="advance">Sort: Advance %</option>
            <option value="rank">Sort: FIFA Rank</option>
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
        <div className="text-center text-[color:var(--color-ink-soft)] py-20">
          <L
            es="Ningún equipo coincide con esos filtros."
            en="No teams match those filters."
          />
        </div>
      )}
    </div>
  );
}
