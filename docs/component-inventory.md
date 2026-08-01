# IamBetterThanMe — Component Inventory
**Session 1 / Phase 0 — Foundation**
*Status: Initial audit. No existing codebase supplied — inventory derived from execution plan screen list + storyboard analysis.*

---

## Source Analysis

**Inputs audited:**
1. Execution plan screen inventory (podcast, post, shop, current/future state, learning-preference, media preference, add friend, dashboard, path tracking/history, payment)
2. Storyboard (12 panels): present self → future self → embrace → energy flow → heal → dissolve → particles merge → confidence → goals surround → guided → walks toward tomorrow

**Finding:** No existing site code available in workspace. All screens will be **built from scratch** against the design system established in this session.

---

## Screen Inventory (from plan)

| Screen | Route (proposed) | Status | Session target |
|--------|------------------|--------|----------------|
| Dashboard (empty state) | `/dashboard` | 🔲 Not built | Session 2 |
| Dashboard (populated) | `/dashboard` | 🔲 Not built | Session 4 |
| Onboarding — Goals capture | `/onboarding/goals` | 🔲 Not built | Session 3 |
| Onboarding — Current self | `/onboarding/present` | 🔲 Not built | Session 3 |
| Onboarding — Future self question | `/onboarding/future` | 🔲 Not built | Session 3 |
| Onboarding — Learning preferences | `/onboarding/learning` | 🔲 Not built | Session 3 |
| Onboarding — Media preferences | `/onboarding/media` | 🔲 Not built | Session 3 |
| Content grid — Film | `/content/film` | 🔲 Not built | Session 5 |
| Content grid — Music | `/content/music` | 🔲 Not built | Session 5 |
| Content grid — Art | `/content/art` | 🔲 Not built | Session 5 |
| Content grid — Animation | `/content/animation` | 🔲 Not built | Session 5 |
| Content grid — Editorial | `/content/editorial` | 🔲 Not built | Session 5 |
| Content grid — Print | `/content/print` | 🔲 Not built | Session 5 |
| Content detail view | `/content/:type/:id` | 🔲 Not built | Session 5 |
| Path tracking | `/path` | 🔲 Not built | Session 5 |
| Path history | `/path/history` | 🔲 Not built | Session 5 |
| Add friend / Social | `/social` | 🔲 Not built | Session 5 |
| Payment method | `/settings/payment` | 🔲 Not built | Session 5 |
| Podcast | `/podcast` | 🔲 Not built | Session 5 |
| Post / Blog | `/post` | 🔲 Not built | Session 5 |
| Shop | `/shop` | 🔲 Not built | Session 5 |
| Agent logs dashboard | `/logs` | 🔲 Not built | Session 6 |
| Privacy/data panel | `/settings/privacy` | 🔲 Not built | Session 16 |

---

## Component Inventory

### Navigation
| Component | Reuse | Build? | Notes |
|-----------|-------|--------|-------|
| `AppShell` | — | Session 2 | Top-level layout wrapper |
| `Sidebar` | — | Session 2 | Collapsible, 280px wide |
| `NavItem` | — | Session 2 | Icon + label, active state |
| `TopBar` | — | Session 2 | Search, notifications, avatar |
| `MobileMenu` | — | Session 2 | Hamburger → drawer |

### Dashboard
| Component | Reuse | Build? | Notes |
|-----------|-------|--------|-------|
| `MetricCard` | — | Session 4 | Curated/Global/Expert/Activities |
| `ProgressRing` | — | Session 4 | SVG circular progress |
| `ActivityFeed` | — | Session 4 | Recent agent actions |
| `AgentThinkingIndicator` | — | Session 2 | 2D pulse placeholder; replaced in Session 13 |
| `RecommendationCard` | — | Session 4 | Media recommendation tile |

### Onboarding
| Component | Reuse | Build? | Notes |
|-----------|-------|--------|-------|
| `OnboardingShell` | — | Session 3 | Step progress, narrative framing |
| `GoalPicker` | — | Session 3 | Multi-select with icons |
| `SelfAssessmentSlider` | — | Session 3 | Present → imagined self axis |
| `LearningStylePicker` | — | Session 3 | Visual/audio/reading/kinesthetic |
| `MediaPreferencePicker` | — | Session 3 | Film/music/art/animation/editorial/print |
| `StepProgress` | — | Session 3 | Top progress bar |

### Content
| Component | Reuse | Build? | Notes |
|-----------|-------|--------|-------|
| `ContentGrid` | — | Session 5 | Responsive masonry-like grid |
| `ContentCard` | — | Session 5 | Thumbnail + metadata |
| `ContentDetail` | — | Session 5 | Full-page detail view |
| `ContentTypeFilter` | — | Session 5 | Tab/pill filter bar |
| `MediaPlayer` | — | Session 5 | Stubbed — no real playback yet |

### Shared / Design System
| Component | Reuse | Build? | Notes |
|-----------|-------|--------|-------|
| `Button` | — | Session 2 | primary/ghost/danger variants |
| `Badge` | — | Session 2 | status, category labels |
| `Avatar` | — | Session 2 | Image + fallback initials |
| `Modal` | — | Session 2 | Animated slide-up |
| `Toast` | — | Session 2 | Success/error/info |
| `Tooltip` | — | Session 2 | Hover labels |
| `Skeleton` | — | Session 2 | Loading placeholder |
| `GlassCard` | — | Session 2 | Glassmorphism container |
| `ParticleCanvas` | — | Session 2 | 2D CSS-only placeholder; 3D in Session 13 |
| `ProgressBar` | — | Session 3 | Linear variant |
| `Tag` | — | Session 3 | Selectable/dismissible |
| `Input` | — | Session 3 | Text, search, textarea |
| `Select` | — | Session 3 | Custom dropdown |

### Agent/Logs (Phase 2)
| Component | Build session | Notes |
|-----------|--------------|-------|
| `LogEntry` | 6 | Tool call, data source, result — structured |
| `ToolCallBadge` | 6 | Identifies which MCP tool ran |
| `DataSourceTag` | 6 | YouTube / Reddit / Web / Internal |
| `MetricsPanel` | 6 | Graphs for agent performance |

### Extension (Phase 3)
| Component | Build session | Notes |
|-----------|--------------|-------|
| `ExtensionPopup` | 7 | Matches design system |
| `TrackingToggle` | 8 | Enable/disable passive capture |
| `SessionSummary` | 8 | What was captured today |
| `SyncStatus` | 9 | Connection status to dashboard |

---

## 3D Moments Shortlist (locked in Session 11)
*Pre-scoped here to avoid scope-creep in Sessions 2–10:*

| # | Moment | Storyboard panels | Trigger | Load-bearing? |
|---|--------|-------------------|---------|---------------|
| A | Agent-thinking loop | (none — UI element) | Every AI operation | **YES** — perf budget critical |
| B | Onboarding ritual | 1–12 (full sequence) | First login / replay | No — decorative |

**Hard rule:** No Three.js imported before Session 11. The `ParticleCanvas` in Session 2 is CSS-only.

---

## Decisions Locked (do not revisit without good cause)

1. **Satoshi** is the brand typeface — no alternatives without explicit decision.
2. Color hue anchor: **250° (indigo-lavender)** — derived from storyboard particle light color.
3. `--ease-particle-merge: cubic-bezier(0.08, 0.82, 0.17, 1.0)` — locked for Phase 5 Three.js.
4. **Manifest V3** for extension — V2 is deprecated.
5. Extension data stored in **IndexedDB** (not localStorage) — larger quota, structured queries.
6. `particleConfig.countHigh/Mid/Low` thresholds — do not change without Phase 5 perf testing.
7. All screens are **built from scratch** (no existing code to port).
