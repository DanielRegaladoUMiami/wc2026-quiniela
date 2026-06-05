import Link from "next/link";
import FlagImg from "./FlagImg";
import ConfederationChip from "./ConfederationChip";
import L from "@/components/L";
import { Team, fmtPct } from "@/lib/types";

export default function TeamCard({ team, priority }: { team: Team; priority?: boolean }) {
  const advance = Math.min(100, Math.max(0, (team.p_advance_group ?? 0) * 100));
  return (
    <Link
      href={`/teams/${team.fifa_code.toLowerCase()}`}
      className="sticker sticker-hover group relative block rounded-none p-4 overflow-hidden"
    >
      <div className="flex items-start gap-3">
        <FlagImg
          iso2={team.iso2}
          size={56}
          priority={priority}
          className="!rounded-none border-2 border-[color:var(--color-ink)] !ring-0"
        />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="display text-lg leading-none truncate text-[color:var(--color-ink)]">{team.team}</h3>
            <ConfederationChip conf={team.conf} size="xs" />
          </div>
          <p className="text-xs text-[color:var(--color-ink-soft)] mt-0.5 truncate italic">{team.nickname}</p>
          <div className="mt-1 flex items-center gap-3 text-[11px] text-[color:var(--color-ink-soft)]">
            <span>FIFA #{team.fifa_rank}</span>
            <span className="text-[color:var(--color-line-soft)]">·</span>
            <span>
              <L es="Grupo" en="Group" /> {team.group}
            </span>
          </div>
        </div>
        <div className="text-right">
          <div className="text-[10px] uppercase tracking-wider text-[color:var(--color-ink-soft)]">
            <L es="Campeón" en="Champion" />
          </div>
          <div className="display text-2xl text-[color:var(--color-red)] tabular-nums">
            {fmtPct(team.p_champion ?? 0, 1)}
          </div>
        </div>
      </div>
      <div className="mt-3">
        <div className="flex justify-between text-[11px] text-[color:var(--color-ink-soft)] mb-1">
          <span>
            <L es="Avanza de grupo" en="Advance from group" />
          </span>
          <span className="text-[color:var(--color-ink)] tabular-nums">{fmtPct(team.p_advance_group ?? 0)}</span>
        </div>
        <div className="relative h-2 border-2 border-[color:var(--color-ink)] bar-track">
          <div
            className="absolute inset-y-0 left-0 bg-[color:var(--color-green)]"
            style={{ width: `${advance}%` }}
          />
        </div>
      </div>
    </Link>
  );
}
