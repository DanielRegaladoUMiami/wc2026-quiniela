import { getTeams } from "@/lib/data";
import TeamsExplorer from "./TeamsExplorer";

export const metadata = { title: "Teams" };

export default function TeamsPage() {
  const teams = getTeams();
  return (
    <div className="mx-auto max-w-7xl px-6 py-12">
      <header className="mb-8">
        <h1 className="display text-5xl sm:text-7xl leading-[0.82] text-[color:var(--color-ink)]">
          THE 48 <span className="text-[color:var(--color-red)]">TEAMS</span>
        </h1>
        <p className="mt-3 max-w-2xl text-sm leading-relaxed text-[color:var(--color-ink-soft)]">
          Every nation that qualified for the expanded 2026 format. Filter by confederation, sort by
          model conviction.
        </p>
      </header>
      <TeamsExplorer teams={teams} />
    </div>
  );
}
