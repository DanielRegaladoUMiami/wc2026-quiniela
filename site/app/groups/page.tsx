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
        <h1 className="font-display text-4xl sm:text-5xl font-bold tracking-tight">Groups</h1>
        <p className="text-slate-400 mt-2 max-w-2xl">
          12 groups of 4. Top 2 from each group advance automatically; the 8 best third-placed teams also progress
          to the Round of 32.
        </p>
      </header>

      <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {labels.map((g) => {
          const teams = groups[g];
          return (
            <div key={g} className="glass rounded-xl p-4">
              <div className="flex items-center justify-between mb-3">
                <h2 className="font-display text-xl font-bold">Group {g}</h2>
                <span className="text-[10px] text-slate-500 uppercase tracking-wider">Advance · 3rd</span>
              </div>
              <div className="space-y-3">
                {teams.map((t) => {
                  const a = adv.get(t.team);
                  return (
                    <Link key={t.fifa_code} href={`/teams/${t.fifa_code.toLowerCase()}`} className="block group">
                      <div className="flex items-center gap-2 mb-1.5">
                        <FlagImg iso2={t.iso2} size={22} />
                        <span className="text-sm font-medium truncate flex-1 group-hover:text-emerald-300">{t.team}</span>
                        <span className="text-xs tabular-nums text-emerald-300">{fmtPct(a?.p_advance_group ?? 0)}</span>
                        <span className="text-[10px] tabular-nums text-amber-400 w-10 text-right">{fmtPct(a?.p_third_place ?? 0)}</span>
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
