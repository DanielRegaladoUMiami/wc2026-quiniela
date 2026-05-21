import Link from "next/link";

const links = [
  { href: "/", label: "Home" },
  { href: "/bracket", label: "Bracket" },
  { href: "/groups", label: "Groups" },
  { href: "/teams", label: "Teams" },
  { href: "/matches", label: "Matches" },
  { href: "/backtest", label: "Backtest" },
  { href: "/methodology", label: "Method" },
  { href: "/about", label: "About" },
];

export default function NavBar() {
  return (
    <header className="sticky top-0 z-40 backdrop-blur-xl bg-[color:var(--color-surface)]/70 border-b border-[color:var(--color-line)]">
      <nav className="mx-auto max-w-7xl px-4 sm:px-6 h-14 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2 group">
          <div className="h-7 w-7 rounded-md bg-gradient-to-br from-emerald-400 to-amber-400 grid place-items-center text-[10px] font-bold text-slate-950">
            WC
          </div>
          <span className="font-display text-sm font-semibold tracking-tight">
            quiniela <span className="text-emerald-400">2026</span>
          </span>
        </Link>
        <ul className="hidden md:flex items-center gap-1 text-sm">
          {links.map((l) => (
            <li key={l.href}>
              <Link
                href={l.href}
                className="px-3 py-1.5 rounded-md text-slate-300 hover:text-white hover:bg-white/5 transition-colors"
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
          className="text-xs text-slate-400 hover:text-white px-3 py-1.5 rounded-md border border-[color:var(--color-line)] hover:border-emerald-500/40"
        >
          GitHub
        </a>
      </nav>
    </header>
  );
}
