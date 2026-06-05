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
      className="grid grid-cols-12 items-center gap-3 px-4 py-3 border-2 border-transparent hover:border-[color:var(--color-ink)] hover:bg-[color:var(--color-card)] transition-colors text-sm"
    >
      <div className="col-span-2 text-[color:var(--color-ink-soft)] text-xs tabular-nums">
        <div>{fmtDate(fixture.date)}</div>
        <div className="text-[color:var(--color-ink-soft)] text-[10px]">M{fixture.num} · {fixture.stage}{fixture.group ? ` ${fixture.group}` : ""}</div>
      </div>
      <div className="col-span-3 flex items-center gap-2 min-w-0">
        {home && <FlagImg iso2={home.iso2} size={28} />}
        <span className="truncate display text-base leading-none">{fixture.home}</span>
      </div>
      <div className="col-span-3 flex items-center gap-2 min-w-0">
        {away && <FlagImg iso2={away.iso2} size={28} />}
        <span className="truncate display text-base leading-none">{fixture.away}</span>
      </div>
      <div className="col-span-3">
        <div className="flex h-2.5 overflow-hidden border-2 border-[color:var(--color-ink)] bar-track">
          <div className="bg-[color:var(--color-blue)]" style={{ width: `${pH * 100}%` }} />
          <div className="bg-[color:var(--color-yellow)]" style={{ width: `${pD * 100}%` }} />
          <div className="bg-[color:var(--color-red)]" style={{ width: `${pA * 100}%` }} />
        </div>
        <div className="flex justify-between text-[10px] mt-1 tabular-nums">
          <span className={pick === "home" ? "text-[color:var(--color-blue)] font-bold" : "text-[color:var(--color-ink-soft)]"}>{fmtPct(pH)}</span>
          <span className={pick === "draw" ? "text-[color:var(--color-ink)] font-bold" : "text-[color:var(--color-ink-soft)]"}>{fmtPct(pD)}</span>
          <span className={pick === "away" ? "text-[color:var(--color-red)] font-bold" : "text-[color:var(--color-ink-soft)]"}>{fmtPct(pA)}</span>
        </div>
      </div>
      <div className="col-span-1 text-right text-xs text-[color:var(--color-ink-soft)] truncate">{fixture.city}</div>
    </Link>
  );
}
