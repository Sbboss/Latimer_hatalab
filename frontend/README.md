# Frontend prototype

Vite + React + TypeScript single-page demo. Renders the hero, live
workspace, dashboard, cockpit, social-evidence and method sections, and
implements the highlight ↔ cockpit interaction.

The frontend is designed around the structured contract in
[`../docs/API_CONTRACT.md`](../docs/API_CONTRACT.md). It can run entirely
on its own using a curated dataset, or talk to the live analysis service
when one is running.

## Run

```bash
npm install
npm run dev
```

Open <http://localhost:5173>.

To produce a static build:

```bash
npm run build
npm run preview
```

## Live vs. curated mode

On load the app calls `GET /api/health` once.

- If the analysis service responds, all subsequent analyses go through
  `POST /api/analyze` and the nav chip reads "Connected · live signals".
- Otherwise the app silently falls back to a local analyzer over the same
  curated dataset and the nav chip reads "Demo mode · curated data".

The fallback path lives in `src/data/mockAnalysis.ts` and produces
output that is byte-shape identical to the live service's response. The
rest of the app does not know which path served the data.

The dev server proxies `/api/*` to `http://localhost:8000` (see
`vite.config.ts`).

## Layout

```
src/
├── App.tsx                    # state machine: input, mode, selection, source
├── main.tsx
├── vite-env.d.ts
├── styles/
│   └── globals.css            # design tokens + every component's styles
├── data/
│   └── mockAnalysis.ts        # curated dataset + offline analyzer
├── lib/
│   ├── types.ts               # frontend mirror of the API contract
│   ├── api.ts                 # fetch client with mock fallback
│   └── segments.ts            # text → highlighted-segment renderer
└── components/
    ├── Nav.tsx                # sticky nav + live/demo status chip
    ├── Hero.tsx               # headline, copy, preview card, timeline mini
    ├── Workspace.tsx          # editor card + dashboard card
    ├── HighlightedText.tsx    # interactive highlights (click → cockpit)
    ├── Dashboard.tsx          # signal strength, dimensions, stats
    ├── Cockpit.tsx            # selected signal explanation + rewrite
    ├── DimensionsBars.tsx     # horizontal bias-dimension bars
    ├── TimelineChart.tsx      # SVG public-attitude timeline
    ├── SocialEvidence.tsx     # 3 evidence cards under workspace
    ├── HowItWorks.tsx         # 4-step method strip
    ├── Footer.tsx
    └── Icons.tsx
```

## Design system

- Palette (Ivory Research):
  - Background `#F7F0E6`
  - Ink `#102033`
  - Accent `#B56A42`
- Typography: IBM Plex Sans (400 / 500 / 600 / 700, plus italic 400 / 500)
  and JetBrains Mono for small labels. No serif display face.
- All styles live in `src/styles/globals.css`. There is no CSS framework.
- All charts (signal strength, dimensions bars, timelines) are inline SVG.
  There is no chart library.

## UI language rules

The visible UI never shows backend codes, model names, route paths,
embedding terminology, or infrastructure jargon. Stick to the user-facing
vocabulary: bias signal strength, hidden assumption, social evidence,
public attitude over time, survey question, suggested rewrite, why this
matters, bias dimensions, GSS-grounded context.

If you add a new field to the API contract, please add a corresponding
human-facing label in the frontend (do not surface the raw key).

## Conventions

- Strict TypeScript (`tsc -b` runs as part of `npm run build`).
- `noUnusedLocals` and `noUnusedParameters` are on; clean up imports as
  you go.
- Components are function components only; no class components.
- State lives in `App.tsx`. Components are presentational and receive
  props.

## Where to extend

- New component: add under `src/components/` and import in `App.tsx`.
- New section style: add tokens to `:root {}` in `globals.css` and use them.
- New evidence card: add an entry to `featuredEvidence` in
  `src/data/mockAnalysis.ts`.
- New phrase / category: add to the glossary in
  `src/data/mockAnalysis.ts` (mock side) and to `_GLOSSARY` in
  `backend/analysis.py` (live side). Keep the two in sync until the live
  detector becomes model-driven.

## Reference files

- `palette.html` — static color-system reference.
- `font-test.html` — typography exploration.

Both live at the root of `frontend/`. Vite does not serve them by default;
open them directly in the browser if needed.
