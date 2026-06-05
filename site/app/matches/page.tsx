import { getFixtures, getMatchProbs, getTeams } from "@/lib/data";
import MatchesTable from "./MatchesTable";

export const metadata = { title: "Matches" };

export default function MatchesPage() {
  const fixtures = getFixtures();
  const probs = getMatchProbs();
  const teams = getTeams();
  return (
    <div className="mx-auto max-w-7xl px-6 py-12">
      <header className="mb-8">
        <h1 className="display text-5xl sm:text-6xl text-[color:var(--color-ink)]">
          THE <span className="text-[color:var(--color-red)]">104 MATCHES</span>
        </h1>
        <p className="mt-2 max-w-2xl text-[color:var(--color-ink-soft)]">
          Every fixture with 1X2 probabilities, expected goals, venue and altitude.
          Filter by stage or group, sort by any column.
        </p>
      </header>
      <MatchesTable fixtures={fixtures} probs={probs} teams={teams} />
    </div>
  );
}
