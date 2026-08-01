# IamBetterThanMe — Design System

## Tokens

The canonical design token source lives in `tokens/`:

- **`design-tokens.css`** — CSS custom properties. Import this globally in the web app. This is the single source of truth.
- **`design-tokens.ts`** — TypeScript mirror. Use in Three.js shaders, JS logic, Chrome extension. Keep in sync with CSS file.

## Typography

**Satoshi** is the brand typeface. Loaded via Fontshare CDN. Fallback stack: `Inter → DM Sans → system-ui`.

Weights available: 300 (Light), 400 (Regular), 500 (Medium), 700 (Bold), 900 (Black).

## Color Palette

Built from the storyboard's particle/energy aesthetic:
- **Surface stack**: 5 levels from `--color-void` (near-black #09090f) to `--color-surface-3` (hover state)
- **Brand primary**: hsl(250°) indigo-lavender — `--color-primary-400` through `--color-primary-900`
- **Particle/Energy colors**: Used in 3D layer (Phase 5) and 2D glow effects
- **Accents**: Cyan (achievement), Silver (neutral), Rose (alert), Gold (milestone)

## Motion Tokens

Critical: **`--ease-particle-merge`** (`cubic-bezier(0.08, 0.82, 0.17, 1.0)`) is locked for Phase 5 Three.js. Do not change it.

| Token | Curve | Use |
|-------|-------|-----|
| `--ease-spring` | `cubic-bezier(0.34, 1.56, 0.64, 1.0)` | UI micro-interactions |
| `--ease-particle-merge` | `cubic-bezier(0.08, 0.82, 0.17, 1.0)` | 3D particle animations |
| `--ease-dissolve` | `cubic-bezier(0.25, 0.46, 0.45, 0.94)` | Future self fade effects |
| `--dur-ritual` | `2400ms` | Onboarding sequence phase duration |

## Glassmorphism

```css
background: var(--glass-bg);       /* hsl(240 15% 9% / 0.7) */
border: 1px solid var(--glass-border); /* hsl(240 40% 50% / 0.15) */
backdrop-filter: var(--glass-blur); /* blur(16px) saturate(1.4) */
```

## Component Library

Components live in `components/`. Built progressively per session (see `../docs/component-inventory.md`).

## Usage Rules

1. Never use hex/rgb color literals in component CSS — always use `var(--color-*)` tokens.
2. Never use px font sizes directly — always use `var(--text-*)` tokens.
3. Never import Three.js before Session 11.
4. CSS vars are canonical. TS mirror must stay in sync.
