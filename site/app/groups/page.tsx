import Link from "next/link";
import FlagImg from "@/components/FlagImg";
import ProbabilityBar from "@/components/ProbabilityBar";
import { teamsByGroup, getAdvancement, fmtPct } from "@/lib/data";

export const metadata = { title: "Groups" };

export default function GroupsPage() {
  const groups = teamsByGroup();
  const adv = new Map(getAdvancement().map((a) => [a.team, a]));
  const labels = Object.keys(groups).sort();

  return (
    <div className="mx-auto max-w-7xl px-6 py-12">
      <header className="mb-8">
        <h1 className="display text-4xl sm:text-5xl tracking-tight text-[color:var(--color-ink)]">GROUPS</h1>
        <p className="text-[color:var(--color-ink-soft)] mt-2 max-w-2xl">
          12 groups of 4. The top 2 from each group advance automatically; the 8 best third-place
          teams also reach the Round of 32.
        </p>
      </header>

      <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {labels.map((g) => {
          const teams = groups[g];
          return (
            <div key={g} className="sticker rounded-none overflow-hidden">
              <div className="halftone flex items-center justify-between gap-2 border-b-2 border-[color:var(--color-ink)] bg-[color:var(--color-red)] px-3 py-1.5 text-[color:var(--color-card)]">
                <h2 className="display text-xl leading-none">Group {g}</h2>
                <span className="display text-[10px] leading-none tracking-wider">Advance · 3rd</span>
              </div>
              <div className="space-y-3 p-4">
                {teams.map((t) => {
                  const a = adv.get(t.team);
                  return (
                    <Link key={t.fifa_code} href={`/teams/${t.fifa_code.toLowerCase()}`} className="block group">
                      <div className="flex items-center gap-2 mb-1.5">
                        <FlagImg iso2={t.iso2} size={22} className="!rounded-none border-2 border-[color:var(--color-ink)] !ring-0" />
                        <span className="text-sm font-medium truncate flex-1 text-[color:var(--color-ink)] group-hover:text-[color:var(--color-red)]">{t.team}</span>
                        <span className="text-xs tabular-nums font-bold text-[color:var(--color-blue)]">{fmtPct(a?.p_advance_group ?? 0)}</span>
                        <span className="text-[10px] tabular-nums text-[color:var(--color-red)] w-10 text-right">{fmtPct(a?.p_third_place ?? 0)}</span>
                      </div>
                      <ProbabilityBar value={a?.p_advance_group ?? 0} color="emerald" height={4} />
                    </Link>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
