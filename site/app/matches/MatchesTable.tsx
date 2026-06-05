"use client";
import { useMemo, useState } from "react";
import L from "@/components/L";
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
        <Chip active={stage === null} onClick={() => setStage(null)}><L es="Todas las fases" en="All stages" /></Chip>
        {stages.map((s) => (
          <Chip key={s} active={stage === s} onClick={() => setStage(s === stage ? null : s)}>{s}</Chip>
        ))}
        <div className="w-px h-5 bg-[color:var(--color-line)] mx-1" />
        <Chip active={group === null} onClick={() => setGroup(null)}><L es="Todos los grupos" en="All groups" /></Chip>
        {groups.map((g) => (
          <Chip key={g} active={group === g} onClick={() => setGroup(g === group ? null : g)}>Grp {g}</Chip>
        ))}
        <input
          placeholder="Team or venue..."
          value={q}
          onChange={(e) => setQ(e.target.value)}
          className="ml-auto bg-[color:var(--color-card)] border-2 border-[color:var(--color-ink)] rounded-none px-3 py-1.5 text-sm w-48 text-[color:var(--color-ink)] placeholder:text-[color:var(--color-ink-soft)] focus:outline-none"
        />
      </div>

      <div className="sticker rounded-none overflow-hidden">
        <div className="halftone grid grid-cols-12 gap-3 px-4 py-2.5 text-[10px] uppercase tracking-wider text-[color:var(--color-card)] bg-[color:var(--color-red)] border-b-2 border-[color:var(--color-ink)]">
          <div className="col-span-2"><L es="Fecha" en="Date" /></div>
          <div className="col-span-3"><L es="Local" en="Home" /></div>
          <div className="col-span-3"><L es="Visitante" en="Away" /></div>
          <div className="col-span-3">1 / X / 2</div>
          <div className="col-span-1 text-right"><L es="Sede" en="Venue" /></div>
        </div>
        <div className="divide-y-2 divide-[color:var(--color-line-soft)]">
          {rows.map((f) => (
            <MatchRow key={f.num} fixture={f} prob={probMap.get(f.num)} teamMap={teamMap} />
          ))}
        </div>
        {rows.length === 0 && <div className="py-20 text-center text-[color:var(--color-ink-soft)] text-sm"><L es="Ningún partido coincide con esos filtros." en="No matches match those filters." /></div>}
      </div>
      <div className="text-xs text-[color:var(--color-ink-soft)] mt-3">{rows.length} <L es="de" en="of" /> {fixtures.length} <L es="partidos" en="matches" /></div>
    </div>
  );
}

function Chip({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      onClick={onClick}
      className={`display text-xs px-3 py-1.5 rounded-none border-2 border-[color:var(--color-ink)] transition-colors ${
        active
          ? "bg-[color:var(--color-ink)] text-[color:var(--color-yellow)]"
          : "bg-[color:var(--color-yellow)] text-[color:var(--color-ink)] hover:bg-[color:var(--color-ink)] hover:text-[color:var(--color-yellow)]"
      }`}
    >
      {children}
    </button>
  );
}
