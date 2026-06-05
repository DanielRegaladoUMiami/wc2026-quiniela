import Link from "next/link";

const links = [
  { href: "/", label: "EDGE" },
  { href: "/bracket", label: "BRACKET" },
  { href: "/groups", label: "GROUPS" },
  { href: "/teams", label: "TEAMS" },
  { href: "/matches", label: "MATCHES" },
  { href: "/backtest", label: "BACKTEST" },
  { href: "/methodology", label: "METHOD" },
];

export default function NavBar() {
  return (
    <header className="sticky top-0 z-40 border-b-2 border-[color:var(--color-ink)] bg-[color:var(--color-red)]">
      <nav className="mx-auto max-w-screen-2xl px-4 sm:px-6 h-12 flex items-center justify-between gap-4">
        <Link href="/" className="display text-2xl leading-none text-[color:var(--color-card)] shrink-0">
          WC26&nbsp;<span className="text-[color:var(--color-yellow)]">QUINIELA</span>
        </Link>
        <ul className="flex items-center gap-0.5 overflow-x-auto">
          {links.map((l) => (
            <li key={l.label}>
              <Link
                href={l.href}
                className="display block px-2.5 py-1 text-sm leading-none whitespace-nowrap text-[color:var(--color-card)] hover:bg-[color:var(--color-ink)] hover:text-[color:var(--color-yellow)] transition-colors"
              >
                {l.label}
              </Link>
            </li>
          ))}
        </ul>
        <a
          href="https://github.com/DanielRegaladoUMiami/wc2026-quiniela"
          target="_blank"
          rel="noreferrer"
          className="display hidden md:block shrink-0 px-2.5 py-1 text-sm leading-none text-[color:var(--color-ink)] bg-[color:var(--color-yellow)] border-2 border-[color:var(--color-ink)] hover:bg-[color:var(--color-card)]"
        >
          GITHUB
        </a>
      </nav>
    </header>
  );
}
