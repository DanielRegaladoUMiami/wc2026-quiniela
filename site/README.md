# wc2026-quiniela · site

Production Next.js 16 (App Router) front-end for the [wc2026-quiniela](https://github.com/DanielRegaladoUMiami/wc2026-quiniela) project. Replaces the Gradio dashboard living in `../web/` with a Vercel-deployable static site inspired by ESPN soccer / Linear / Vercel design quality.

## Stack
- **Next.js 16** + **TypeScript** (App Router, Turbopack)
- **Tailwind CSS 4** (theme tokens: emerald / amber / slate)
- **Framer Motion** for probability bar animations
- **Recharts** for donut + cumulative log-loss charts
- **react-katex** for math rendering on `/methodology`
- **Geist** + **Space Grotesk** via `next/font`

## Data pipeline
Parquet → JSON happens **at build time** via `scripts/parquet_to_json.py`, executed by the npm `prebuild` hook. The Next app reads only static JSON at runtime — no parquet libs ship to the client.

```
/data/sims/sim_run_202605190049/*.parquet
    │  python3 scripts/parquet_to_json.py
    ▼
/site/public/data/*.json    (~100 KB total)
    │  fs.readFileSync (server-only via lib/data.ts)
    ▼
React Server Components → static HTML
```

## Develop / build

```bash
cd site
npm install
npm run dev               # http://localhost:3000
npm run build && npm run start
```

The build produces 163 statically prerendered routes (1 home + 48 teams + 104 matches + 10 other pages).

## Pages
- `/` — Hero, countdown to 2026-06-11 kickoff, top-8 champion bars, opening fixtures.
- `/teams` — All 48 cards, confederation chips, sort/search.
- `/teams/[fifa_code]` — Team profile, advancement waterfall, group fixtures, rivals.
- `/groups` — 12 group cards with advancement bars.
- `/matches` — Sortable / filterable table of all 104 matches.
- `/matches/[num]` — 1X2 donut, Dixon-Coles score-matrix heatmap, venue card.
- `/bracket` — Custom-SVG funnel of P(reach round) for top 16.
- `/backtest` — RPS / log-loss for WC22 + Euro24, cumulative log-loss chart.
- `/methodology` — KaTeX-rendered model write-up.
- `/about` — Daniel Regalado, Apache 2.0, disclaimer.

## Deploy to Vercel

```bash
npm i -g vercel
cd site
vercel link
vercel deploy --prod
```

Build command: `npm run build`. Python 3 must be available on the build container to run the parquet→JSON step (Vercel images include it). Alternatively, commit `site/public/data/*.json` so the `prebuild` step is a no-op on the Vercel runner.

## License
Apache 2.0 — see repository root.
