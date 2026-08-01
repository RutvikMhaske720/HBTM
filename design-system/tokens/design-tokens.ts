/**
 * IamBetterThanMe — Design Tokens (TypeScript mirror)
 * Session 1 / Phase 0
 *
 * Keep this in sync with design-tokens.css.
 * Used by: Three.js shaders (Phase 5), extension popup (Phase 3),
 * any JS logic that needs color/motion values.
 *
 * Rule: CSS vars are canonical. This file is derived from them.
 * If CSS vars change, update here too.
 */

export const colors = {
  // Surfaces
  void:       '#09090f',
  surface0:   '#0d0d15',
  surface1:   '#131320',
  surface2:   '#1a1a26',
  surface3:   '#262636',
  border:     '#303044',
  borderGlow: '#2d2d7a',

  // Particle / Energy (critical for Three.js Phase 5)
  particleCore:  '#d4e4fc',
  particleMid:   '#b3b3f5',
  particleOuter: '#8080cc',
  energy:        '#99ddff',

  // Brand primary (HSL: 250° family)
  primary400: '#6b5de8',
  primary500: '#5241d6',
  primary600: '#4236b0',

  // Accents
  accentCyan:   '#34d8e0',
  accentSilver: '#d1d5e8',
  accentRose:   '#f06292',
  accentGold:   '#f5c842',

  // Text
  textPrimary:   '#e8eaf0',
  textSecondary: '#9a9db8',
  textMuted:     '#686a80',

  // Status
  success: '#34c76b',
  warning: '#f5c030',
  error:   '#e05555',
  info:    '#4aabf5',
} as const;

export const easing = {
  // Standard CSS strings — pass directly to CSS transition/animation
  spring:        'cubic-bezier(0.34, 1.56, 0.64, 1.0)',
  /**
   * particleMerge: slow start → fast convergence → gentle settle.
   * Locked for Phase 5 Three.js usage. Do not modify.
   */
  particleMerge: 'cubic-bezier(0.08, 0.82, 0.17, 1.0)',
  dissolve:      'cubic-bezier(0.25, 0.46, 0.45, 0.94)',
  out:           'cubic-bezier(0.0, 0.0, 0.2, 1.0)',
  inOut:         'cubic-bezier(0.4, 0.0, 0.2, 1.0)',
} as const;

export const duration = {
  instant:   50,
  fast:      150,
  normal:    250,
  slow:      400,
  slower:    600,
  cinematic: 1200,
  ritual:    2400, // onboarding sequence per-phase duration (ms)
} as const;

export const typography = {
  fontSans: "'Satoshi', 'Inter', 'DM Sans', system-ui, sans-serif",
  fontMono: "'JetBrains Mono', 'Fira Code', monospace",
  scale: {
    xs:  '0.8rem',
    sm:  '1rem',
    md:  '1.25rem',
    lg:  '1.563rem',
    xl:  '1.953rem',
    '2xl': '2.441rem',
    '3xl': '3.052rem',
    '4xl': '3.815rem',
  },
} as const;

/** 
 * Three.js particle system config — pre-seeded for Phase 5.
 * Change here, not in shader files, to keep a single source of truth.
 */
export const particleConfig = {
  defaultColor:   0xd4e4fc, // particleCore in hex int
  glowColor:      0xb3b3f5, // particleMid
  outerGlowColor: 0x8080cc, // particleOuter
  energyColor:    0x99ddff,

  // Counts (performance budget — tested in Session 15)
  countHigh:   12000, // high-end device
  countMid:    6000,  // mid device
  countLow:    2000,  // low-power fallback

  // Agent-thinking loop (load-bearing — shown every session)
  thinkingRadius:    1.8,
  thinkingSpeed:     0.6,
  thinkingPulseHz:   1.2,

  // Onboarding ritual (decorative — can be heavier)
  ritualRadius:      3.5,
  ritualDuration:    duration.ritual, // ms
  mergeEasing:       easing.particleMerge,
} as const;

export type Colors = typeof colors;
export type Easing = typeof easing;
