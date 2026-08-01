"use client";

import { useMemo, useRef, useState } from "react";
import { useMotionValueEvent, useScroll, useTransform } from "framer-motion";

/**
 * Placeholder storyboard data standing in for the real 12-photo sequence
 * (present-self -> future-self -> merge -> confident walk into the city).
 * Swap `art` for a real <img src="/hero/frame-XX.jpg" /> per frame once the
 * photography is exported — the scroll-pacing logic below doesn't change.
 */
const FRAMES: { caption: string; glow: { x: number; y: number; r: number }[] }[] = [
  { caption: "She is her present self.", glow: [{ x: 42, y: 60, r: 26 }] },
  { caption: "Her future self appears.", glow: [{ x: 40, y: 58, r: 22 }, { x: 66, y: 46, r: 20 }] },
  { caption: "Future self reaches out with love.", glow: [{ x: 44, y: 56, r: 22 }, { x: 60, y: 48, r: 24 }] },
  { caption: "They embrace.", glow: [{ x: 50, y: 52, r: 34 }] },
  { caption: "Light and energy flow into her.", glow: [{ x: 50, y: 50, r: 40 }] },
  { caption: "She begins to heal and relax.", glow: [{ x: 50, y: 52, r: 36 }] },
  { caption: "Future self dissolves into particles.", glow: [{ x: 50, y: 48, r: 44 }] },
  { caption: "Particles merge into her.", glow: [{ x: 50, y: 50, r: 30 }] },
  { caption: "She opens her eyes with confidence.", glow: [{ x: 50, y: 44, r: 22 }] },
  { caption: "Her goals, habits and dreams surround her.", glow: [{ x: 30, y: 30, r: 14 }, { x: 70, y: 34, r: 14 }, { x: 50, y: 66, r: 14 }] },
  { caption: "She is guided by her future.", glow: [{ x: 50, y: 50, r: 24 }] },
  { caption: "She walks towards her better tomorrow.", glow: [{ x: 50, y: 70, r: 50 }] },
];

// Pacing: groups of [2 fast, 3 slow] transitions repeating across the 12 frames.
const FAST = 1;
const SLOW = 2.5;
const TRANSITION_WEIGHTS = [FAST, SLOW, SLOW, SLOW, FAST, FAST, SLOW, SLOW, SLOW, FAST, FAST];

function useBreakpoints() {
  return useMemo(() => {
    const cumulative = [0];
    TRANSITION_WEIGHTS.forEach((w) => cumulative.push(cumulative[cumulative.length - 1] + w));
    const total = cumulative[cumulative.length - 1];
    return cumulative.map((v) => v / total);
  }, []);
}

function StoryFrame({ frame, style }: { frame: (typeof FRAMES)[number]; style: React.CSSProperties }) {
  return (
    <div className="absolute inset-0" style={style}>
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_#1c1c1c_0%,_#0d0d0d_70%)]" />
      {frame.glow.map((g, i) => (
        <div
          key={i}
          className="absolute rounded-full bg-white/70 blur-3xl"
          style={{
            left: `${g.x}%`,
            top: `${g.y}%`,
            width: `${g.r}%`,
            height: `${g.r}%`,
            transform: "translate(-50%, -50%)",
          }}
        />
      ))}
      <p className="absolute bottom-10 left-1/2 w-full max-w-md -translate-x-1/2 text-center text-sm tracking-wide text-white/60">
        {frame.caption}
      </p>
    </div>
  );
}

export default function HeroSequence({ children }: { children: React.ReactNode }) {
  const trackRef = useRef<HTMLDivElement>(null);
  const breakpoints = useBreakpoints();
  const outputRange = useMemo(() => FRAMES.map((_, i) => i), []);

  const { scrollYProgress } = useScroll({
    target: trackRef,
    offset: ["start start", "end end"],
  });

  const frameFloat = useTransform(scrollYProgress, breakpoints, outputRange);
  const [position, setPosition] = useState(0);
  useMotionValueEvent(frameFloat, "change", (v) => setPosition(v));

  const clamped = Math.min(Math.max(position, 0), FRAMES.length - 1);
  const currentIndex = Math.floor(clamped);
  const nextIndex = Math.min(currentIndex + 1, FRAMES.length - 1);
  const blend = clamped - currentIndex;

  return (
    <div ref={trackRef} style={{ height: "520vh" }} className="relative">
      <div className="sticky top-0 h-screen w-full overflow-hidden bg-(--color-ink)">
        <StoryFrame frame={FRAMES[currentIndex]} style={{ opacity: 1 - blend }} />
        {nextIndex !== currentIndex && (
          <StoryFrame frame={FRAMES[nextIndex]} style={{ opacity: blend }} />
        )}

        {/* Opacity is intentionally reduced + scrimmed so headline copy stays legible */}
        <div className="absolute inset-0 bg-(--color-ink)/55" />
        <div className="absolute inset-0 bg-gradient-to-b from-(--color-ink)/40 via-transparent to-(--color-ink)/70" />

        <div className="relative z-10 flex h-full flex-col items-center justify-center px-6 text-center">
          {children}
        </div>
      </div>
    </div>
  );
}
