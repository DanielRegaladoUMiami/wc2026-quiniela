import { getTeams } from "@/lib/data";
import TeamsExplorer from "./TeamsExplorer";

export const metadata = { title: "Teams" };

export default function TeamsPage() {
  const teams = getTeams();
  return (
    <div className="mx-auto max-w-7xl px-6 py-12">
      <header className="mb-8">
        <h1 className="font-display text-4xl sm:text-5xl font-bold tracking-tight">All 48 teams</h1>
        <p className="text-slate-400 mt-2 max-w-2xl">
          Every nation that qualified for the 2026 expanded format. Filter by confederation, sort by
          model conviction.
        </p>
      </header>
      <TeamsExplorer teams={teams} />
    </div>
  );
}
