# IABTM — Project State

Tracks what's actually built vs. what `implementation_plan.md` describes.
The full plan (multi-agent LangGraph backend, MCP servers, Chrome
extension, desktop tracker, payments, etc.) is a multi-month build. This
session scoped down to the plan's own stated MVP: an interactive
Next.js/TypeScript UI/UX prototype, starting with the two flows we had
concrete visual references for.

## Stack

Next.js 16 (App Router) + TypeScript + Tailwind v4 + Framer Motion.
Single app, no monorepo (the earlier "Phase 0" monorepo scaffold —
`design-system/`, `docs/component-inventory.md` — was superseded; those
files are gone from the working tree but still in git history at
`9c1c712` if anything needs to be recovered from them).

Run it:

```bash
npm install
npm run dev   # http://localhost:3000
```

## Built this session

- **Landing page** (`src/app/page.tsx`, `src/components/HeroSequence.tsx`)
  - Navbar with the real IABTM nav items and a **"Let's grow"** CTA in
    place of Sign in (per your note — no auth for this synthetic-data
    prototype phase).
  - Scroll-driven hero: a 12-frame storyboard sequence that steps
    forward as the user scrolls, paced in groups (2 fast transitions,
    3 slow, repeating) via weighted breakpoints in
    `HeroSequence.tsx`. Background opacity is knocked down + scrimmed
    so "I am better than me" stays legible on top.
  - **Placeholder frames**: the 12 storyboard images you shared aren't
    saved as files anywhere I can read them from — I only see them
    inline in chat. The 12 frames are currently rendered as abstract
    dark/glow placeholders with the storyboard's own captions ("She is
    her present self." → "She walks towards her better tomorrow.") so
    the scroll mechanism is fully demonstrable. **To get the real
    photos in**: export/save that sprite sheet as 12 image files (or
    one file per frame) into `public/hero/`, then swap the `<StoryFrame>`
    render in `HeroSequence.tsx` for an `<img>` tag — the pacing logic
    doesn't change.
  - Satoshi font isn't available in this sandbox either — `layout.tsx`
    aliases the `--font-satoshi` variable to Geist as a stand-in. Drop
    the real `Satoshi-Variable.woff2` into `public/fonts/` and swap the
    `next/font/google` call for a `next/font/local` one to match spec
    section 5.1 exactly.
- **Onboarding flow** (`src/app/onboarding/page.tsx`), 5 steps, no
  auth/password gate:
  1. Current self / imagined self attribute picker ("Me" / "I Am")
  2. Learning style
  3. Media preferences
  4. Profile info — name, profile name, email, phone, photo. **Password
     field removed** (this was the "signin" piece — dropped per your
     instruction since this is for synthetic test data, not real
     accounts).
  5. Goals + timeline (from the plan's spec — the real product screens
     you shared didn't include this step, but the recommendation engine
     needs it, so it's here to close the loop)
  - Ends in a simulated "AI Curator is analyzing your profile…"
    thinking animation, then 5 growth-scored recommendation cards with
    "why this?" copy — satisfies MVP goals #2/#3 from the plan without
    a real backend (all data is static/local state).

Verified in a headless browser this session: both pages render with
zero console/page errors, the scroll animation visibly steps through
frames, and the full 5-step onboarding flow (fill → continue → reveal)
completes end to end.

## Explicitly not attempted this session

Everything backend/infra from the plan — LangGraph agents, MCP servers,
Identity Graph persistence, Chrome extension, desktop tracker, real
auth, payments, Shopify — is spec-only in `implementation_plan.md`.
The dashboard, Agent Lab log viewer, Path View, and Identity Graph
visualization (plan sections 4.2.3–4.2.7) also aren't built yet — the
onboarding reveal screen's "Enter your dashboard" button currently just
links back to `/`.

## Suggested next steps

1. Drop in the real hero photography and Satoshi font (see above).
2. Build the Dashboard shell (4.2.3) as static/local-state, same
   pattern as onboarding — no backend needed for a UI prototype.
3. Only after the UI prototype is validated: start the LangGraph
   orchestrator + one MCP server (Internal DB) as a real backend slice.
