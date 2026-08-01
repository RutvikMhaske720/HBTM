# IamBetterThanMe (HBTM) — Monorepo

> A multi-agent personal growth recommendation engine with a rich web UI, Chrome extension, and 3D visualization layer.

## Structure

```
/HBTM
├── web/              — Main React + Vite web application
├── extension/        — Chrome Extension (Manifest V3)
├── design-system/    — Shared tokens, components, and guidelines
│   ├── tokens/       — design-tokens.css + design-tokens.ts
│   └── components/   — Shared component library (Phase 1+)
└── docs/             — Project documentation
    ├── PROJECT_STATE.md        — Living session handoff doc (READ FIRST)
    └── component-inventory.md — Screen + component build plan
```

## Build Order (see PROJECT_STATE.md for current phase)

| Phase | What |
|-------|------|
| 0 | Foundation — tokens, scaffold (✅ DONE) |
| 1 | Core Web UI/UX — Sessions 2–5 |
| 2 | Agent Logs Dashboard — Session 6 |
| 3 | Chrome Extension — Sessions 7–9 |
| 4 | Integration Pass — Session 10 |
| 5 | 3D UI Layer — Sessions 11–15 |
| 6 | Privacy/Security UI — Session 16 |

## Key Decisions

- **Font**: Satoshi (Fontshare) — no substitutes
- **Colors**: hsl(250°) indigo-lavender anchor
- **Easing**: `--ease-particle-merge: cubic-bezier(0.08, 0.82, 0.17, 1.0)` — locked for Three.js Phase 5
- **Extension**: Manifest V3 / IndexedDB
- **3D**: Three.js / React Three Fiber — Phase 5 ONLY

## Getting Started (Session 2+)

```bash
# Web app
cd web && npm install && npm run dev

# Extension
cd extension && npm install && npm run build
# Load unpacked from extension/dist in chrome://extensions
```

## Design System

Import design tokens in your app's root CSS:
```css
@import '../design-system/tokens/design-tokens.css';
```

For TypeScript / Three.js:
```ts
import { colors, easing, particleConfig } from '../design-system/tokens/design-tokens';
```
