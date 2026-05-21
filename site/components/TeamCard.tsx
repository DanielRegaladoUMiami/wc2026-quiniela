import Link from "next/link";
import FlagImg from "./FlagImg";
import ConfederationChip from "./ConfederationChip";
import ProbabilityBar from "./ProbabilityBar";
import { Team, fmtPct } from "@/lib/types";

export default function TeamCard({ team, priority }: { team: Team; priority?: boolean }) {
  return (
    <Link
      href={`/teams/${team.fifa_code.toLowerCase()}`}
      className="group relative rounded-xl glass p-4 hover:border-emerald-500/30 hover:bg-white/[0.03] transition-all overflow-hidden"
    >
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-emerald-400/40 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
      <div className="flex items-start gap-3">
        <FlagImg iso2={team.iso2} size={56} priority={priority} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="font-display font-semibold tracking-tight truncate">{team.team}</h3>
            <ConfederationChip conf={team.conf} size="xs" />
          </div>
          <p className="text-xs text-slate-400 mt-0.5 truncate italic">{team.nickname}</p>
          <div className="mt-1 flex items-center gap-3 text-[11px] text-slate-500">
            <span>FIFA #{team.fifa_rank}</span>
            <span className="text-slate-700">·</span>
            <span>Group {team.group}</span>
          </div>
        </div>
        <div className="text-right">
          <div className="text-[10px] uppercase tracking-wider text-slate-500">Champion</div>
          <div className="font-display text-xl font-bold gradient-text tabular-nums">
            {fmtPct(team.p_champion ?? 0, 1)}
          </div>
        </div>
      </div>
      <div className="mt-3">
        <ProbabilityBar
          value={team.p_advance_group ?? 0}
          color="emerald"
          label="Advance from group"
          rightLabel={fmtPct(team.p_advance_group ?? 0)}
          height={6}
        />
      </div>
    </Link>
  );
}
