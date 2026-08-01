# IamBetterThanMe — PROJECT STATE

> **Rule:** Read this at the start of every session. Update it at the end. Commit after update.
> This file is the project's memory. If it's stale, something went wrong.

---

## Current Phase / Session

**Phase 0 — Foundation | Session 1 COMPLETE**
Next: **Phase 1 / Session 2 — App Shell & Navigation**

---

## What Exists and Works

### Repository Structure
```
/HBTM
├── web/
│   └── src/
│       ├── components/    (empty — Session 2+)
│       ├── pages/         (empty — Session 2+)
│       ├── hooks/         (empty)
│       ├── utils/         (empty)
│       └── assets/        (empty)
├── extension/
│   └── src/               (empty — Session 7+)
├── design-system/
│   ├── tokens/
│   │   ├── design-tokens.css   ✅ COMPLETE
│   │   └── design-tokens.ts    ✅ COMPLETE
│   └── components/             (empty — Session 2+)
└── docs/
    ├── component-inventory.md  ✅ COMPLETE
    └── PROJECT_STATE.md        ✅ (this file)
```

### Assets
- Hero brand visual generated: `hbtm_hero_banner` (particle silhouette woman, near-black bg)
- Storyboard: 12-panel sequence (present self → future self → embrace → energy → goals) — audited and referenced in design decisions

### Design System (design-tokens.css + design-tokens.ts)
- ✅ Satoshi font loaded via Fontshare CDN
- ✅ Full type scale (Major Third ratio, 9 steps)
- ✅ Color palette (surface stack, particle/energy colors, primary brand, accents, status)
- ✅ 8pt spacing grid (space-1 through space-32)
- ✅ Border radius scale
- ✅ Shadow tokens including glow variants (for particle effects)
- ✅ Motion/easing tokens including `--ease-particle-merge` (locked for Phase 5 Three.js)
- ✅ Z-index scale (including z-particle layer)
- ✅ Glassmorphism helpers
- ✅ Gradient tokens
- ✅ TypeScript mirror with Three.js `particleConfig` pre-seeded

---

## What's Stubbed (Fake Data, No Real Logic)

**Everything.** Session 1 is scaffold-only. No UI components, no routes, no agent logic.

---

## Design Decisions Locked In (Don't Revisit Without Reason)

| # | Decision | Why locked |
|---|----------|------------|
| 1 | **Satoshi** typeface (Fontshare CDN) | Brand identity, storyboard aesthetic match |
| 2 | Color anchor **hsl(250°)** — indigo/lavender | Matches particle light color in storyboard panels 5-8 |
| 3 | `--ease-particle-merge: cubic-bezier(0.08, 0.82, 0.17, 1.0)` | Phase 5 Three.js must use this exact curve. Change = re-do keyframes |
| 4 | **Manifest V3** for Chrome extension | V2 deprecated by Chrome |
| 5 | Extension storage: **IndexedDB** (not localStorage) | Quota, structured queries needed for agent event shape |
| 6 | Particle counts: high=12000, mid=6000, low=2000 | Pre-seeded for Phase 5 perf budget. Validate in Session 15 |
| 7 | **No Three.js before Session 11** | Prevents scope-creep; 2D CSS placeholder in Session 2 |
| 8 | All screens built from scratch | No existing codebase to port |
| 9 | Two 3D moments only: agent-thinking loop + onboarding ritual | All other 3D deferred to post-Phase 5 |
| 10 | TypeScript token mirror kept in sync with CSS vars | CSS is canonical; TS derived |

---

## Screen Inventory (status snapshot)

23 screens identified (see `docs/component-inventory.md` for full table).
All status: 🔲 Not built.

**Build order:**
- Session 2: App shell, nav, dashboard empty state, AgentThinkingIndicator (2D)
- Session 3: Onboarding flow (5 screens)
- Session 4: Dashboard populated (4 metrics wired to mock data)
- Session 5: Content/social/payment/podcast/shop screens
- Session 6: Agent logs dashboard
- Session 7-9: Chrome extension
- Session 10: Integration pass
- Session 11-15: 3D layer
- Session 16: Privacy UI

---

## Next Session: Start Here (Session 2)

**Goal:** App shell + navigation + dashboard empty state + 2D AgentThinkingIndicator

**First steps:**
1. Read this file ✓ (you're doing it)
2. Init web app — use Vite + React + TypeScript: `npx -y create-vite@latest ./web -- --template react-ts`
3. Install dependencies: `react-router-dom`, `framer-motion` (for 2D animations — NOT Three.js)
4. Import `design-tokens.css` as global stylesheet first, before any component CSS
5. Build in this order: `AppShell` → `Sidebar` → `TopBar` → `NavItem` → basic `Button`/`GlassCard` → Dashboard shell
6. `AgentThinkingIndicator`: CSS keyframe pulse + rotating particles, no canvas API, no Three.js

**Things to NOT do in Session 2:**
- No Three.js, no canvas API (that's Session 11+)
- No real API calls or agent logic
- No onboarding screens (that's Session 3)
- No extension code

**Handoff test for Session 2:**
- Can click through nav items and see route change
- Dashboard shows empty state with correct layout grid
- AgentThinkingIndicator animates on demand
- Responsive: works at 1440px, 1024px, 768px, 375px

---

## Agent Wiring Seams (don't close these off)

These are the places where real backend will attach. Keep them as clean interfaces:

| Seam | Location | Agent consumer |
|------|----------|----------------|
| `AgentThinkingIndicator` state prop | Dashboard | LangGraph orchestrator status |
| Dashboard metrics props | MetricCard components | Real metric queries |
| Agent logs data shape | Session 6 LogEntry component | MCP tool-call logs |
| Extension event shape | IndexedDB schema | LangGraph input pipeline |
| Recommendation card data | ContentGrid | Agent recommendation output |

---

## Git Log
```
[Session 1] Phase 0 foundation — design tokens, component inventory, PROJECT_STATE
```
