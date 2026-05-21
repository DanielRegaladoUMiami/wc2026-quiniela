"use client";
import { useMemo, useState } from "react";
import MatchRow from "@/components/MatchRow";
import { Fixture, MatchProb, Team } from "@/lib/types";

export default function MatchesTable({
  fixtures,
  probs,
  teams,
}: {
  fixtures: Fixture[];
  probs: MatchProb[];
  teams: Team[];
}) {
  const teamMap = useMemo(() => new Map(teams.map((t) => [t.team, t])), [teams]);
  const probMap = useMemo(() => new Map(probs.map((p) => [p.num, p])), [probs]);

  const stages = useMemo(() => Array.from(new Set(fixtures.map((f) => f.stage))), [fixtures]);
  const groups = useMemo(
    () => Array.from(new Set(fixtures.map((f) => f.group).filter(Boolean))).sort() as string[],
    [fixtures],
  );

  const [stage, setStage] = useState<string | null>(null);
  const [group, setGroup] = useState<string | null>(null);
  const [q, setQ] = useState("");

  const rows = useMemo(() => {
    let arr = fixtures.slice();
    if (stage) arr = arr.filter((f) => f.stage === stage);
    if (group) arr = arr.filter((f) => f.group === group);
    if (q) {
      const qq = q.toLowerCase();
      arr = arr.filter(
        (f) => f.home.toLowerCase().includes(qq) || f.away.toLowerCase().includes(qq) || f.city.toLowerCase().includes(qq),
      );
    }
    arr.sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime() || a.num - b.num);
    return arr;
  }, [fixtures, stage, group, q]);

  return (
    <div>
      <div className="flex flex-wrap gap-2 items-center mb-6">
        <Chip active={stage === null} onClick={() => setStage(null)}>All stages</Chip>
        {stages.map((s) => (
          <Chip key={s} active={stage === s} onClick={() => setStage(s === stage ? null : s)}>{s}</Chip>
        ))}
        <div className="w-px h-5 bg-[color:var(--color-line)] mx-1" />
        <Chip active={group === null} onClick={() => setGroup(null)}>All groups</Chip>
        {groups.map((g) => (
          <Chip key={g} active={group === g} onClick={() => setGroup(g === group ? null : g)}>Grp {g}</Chip>
        ))}
        <input
          placeholder="Team or city..."
          value={q}
          onChange={(e) => setQ(e.target.value)}
          className="ml-auto bg-white/5 border border-[color:var(--color-line)] rounded-md px-3 py-1.5 text-sm w-48 focus:outline-none focus:border-emerald-500/40"
        />
      </div>

      <div className="glass rounded-xl overflow-hidden">
        <div className="grid grid-cols-12 gap-3 px-4 py-2.5 text-[10px] uppercase tracking-wider text-slate-500 border-b border-[color:var(--color-line)]">
          <div className="col-span-2">Date</div>
          <div className="col-span-3">Home</div>
          <div className="col-span-3">Away</div>
          <div className="col-span-3">1 / X / 2</div>
          <div className="col-span-1 text-right">Venue</div>
        </div>
        <div className="divide-y divide-[color:var(--color-line)]/50">
          {rows.map((f) => (
            <MatchRow key={f.num} fixture={f} prob={probMap.get(f.num)} teamMap={teamMap} />
          ))}
        </div>
        {rows.length === 0 && <div className="py-20 text-center text-slate-500 text-sm">No matches match those filters.</div>}
      </div>
      <div className="text-xs text-slate-500 mt-3">{rows.length} of {fixtures.length} matches</div>
    </div>
  );
}

function Chip({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      onClick={onClick}
      className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
        active ? "bg-emerald-500/10 border-emerald-500/40 text-emerald-300" : "border-[color:var(--color-line)] text-slate-400 hover:text-white hover:border-white/20"
      }`}
    >
      {children}
    </button>
  );
}
