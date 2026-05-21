import Link from "next/link";
import FlagImg from "./FlagImg";
import { fmtPct, MatchProb, Fixture, Team } from "@/lib/types";
import { fmtDate } from "@/lib/utils";

export default function MatchRow({
  fixture,
  prob,
  teamMap,
}: {
  fixture: Fixture;
  prob?: MatchProb;
  teamMap: Map<string, Team>;
}) {
  const home = teamMap.get(fixture.home);
  const away = teamMap.get(fixture.away);
  const pH = prob?.p_home_win ?? 0;
  const pD = prob?.p_draw ?? 0;
  const pA = prob?.p_away_win ?? 0;
  const pick = pH > pD && pH > pA ? "home" : pA > pD ? "away" : "draw";

  return (
    <Link
      href={`/matches/${fixture.num}`}
      className="grid grid-cols-12 items-center gap-3 px-4 py-3 rounded-lg hover:bg-white/[0.025] border border-transparent hover:border-[color:var(--color-line)] transition-colors text-sm"
    >
      <div className="col-span-2 text-slate-400 text-xs tabular-nums">
        <div>{fmtDate(fixture.date)}</div>
        <div className="text-slate-600 text-[10px]">M{fixture.num} · {fixture.stage}{fixture.group ? ` ${fixture.group}` : ""}</div>
      </div>
      <div className="col-span-3 flex items-center gap-2 min-w-0">
        {home && <FlagImg iso2={home.iso2} size={28} />}
        <span className="truncate font-medium">{fixture.home}</span>
      </div>
      <div className="col-span-3 flex items-center gap-2 min-w-0">
        {away && <FlagImg iso2={away.iso2} size={28} />}
        <span className="truncate font-medium">{fixture.away}</span>
      </div>
      <div className="col-span-3">
        <div className="flex h-2 overflow-hidden rounded-full ring-1 ring-white/5">
          <div className="bg-emerald-500" style={{ width: `${pH * 100}%` }} />
          <div className="bg-slate-500" style={{ width: `${pD * 100}%` }} />
          <div className="bg-amber-400" style={{ width: `${pA * 100}%` }} />
        </div>
        <div className="flex justify-between text-[10px] mt-1 tabular-nums">
          <span className={pick === "home" ? "text-emerald-300 font-medium" : "text-slate-500"}>{fmtPct(pH)}</span>
          <span className={pick === "draw" ? "text-slate-200 font-medium" : "text-slate-500"}>{fmtPct(pD)}</span>
          <span className={pick === "away" ? "text-amber-300 font-medium" : "text-slate-500"}>{fmtPct(pA)}</span>
        </div>
      </div>
      <div className="col-span-1 text-right text-xs text-slate-400 truncate">{fixture.city}</div>
    </Link>
  );
}
