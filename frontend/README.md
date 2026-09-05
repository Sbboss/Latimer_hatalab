# Frontend prototype

Vite + React + TypeScript single-page demo. Renders the hero, live
workspace, Insight Board, social-evidence, and method sections, and
implements the highlight ↔ Insight Board interaction.

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
  curated dataset while keeping infrastructure state out of the interface.

The fallback path lives in `src/data/mockAnalysis.ts` and produces
output that is byte-shape identical to the live service's response. The
rest of the app does not know which path served the data.

The dev server proxies `/api/*` to `http://localhost:8001` (see
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
│   ├── modelOrder.ts          # stable GPT/Claude/DeepSeek/Llama order
│   └── segments.ts            # text → highlighted-segment renderer
└── components/
    ├── About.tsx              # Ray Fouché and HAT Lab product philosophy
    ├── Nav.tsx                # compact sticky navigation
    ├── Hero.tsx               # headline, copy, and reflective signal preview
    ├── Workspace.tsx          # editor card + dashboard card
    ├── HighlightedText.tsx    # interactive highlights (click → Insight Board)
    ├── Dashboard.tsx          # signal strength, dimensions, stats
    ├── CoverageChart.tsx      # ISSP measurement and response-scale profile
    ├── InsightBoard.tsx       # selected signal explanation + rewrite
    ├── DimensionsBars.tsx     # horizontal bias-dimension bars
    ├── TimelineChart.tsx      # SVG public-attitude timeline
    ├── SocialEvidence.tsx     # up to two real GSS + two real ISSP questions
    ├── SurveyQuestion.tsx     # plain wording + expandable original source
    ├── HowItWorks.tsx         # legacy method component, excluded from the homepage
    ├── Footer.tsx
    └── Icons.tsx
```

## Design system

- Palette: neutral system surfaces with ink `#17191F` and a restrained
  slate-blue accent `#596B9F`.
- Typography: the native system sans-serif stack, with SF Pro on Apple
  platforms and platform-appropriate fallbacks elsewhere.
- All styles live in `src/styles/globals.css`. There is no CSS framework.
- Response timelines use inline SVG. Records without response percentages
  use a factual measurement profile instead of a decorative chart.
- Model cards stay in one horizontal, scrollable comparison row.
- User-triggered analysis shows in-place progress and visual/audio completion feedback without moving the page.
- Technical ISSP wording is simplified for the primary view while the original survey text and source identifiers remain available on demand.
  There is no chart library.

## UI language rules

The visible UI never shows backend codes, deployment names, route paths,
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
