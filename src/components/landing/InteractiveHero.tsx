"use client";

import { useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { LANDING_DOMAINS } from "@/lib/landingDomains";
import MagneticButton from "./MagneticButton";

export default function InteractiveHero({
  children,
}: {
  children: React.ReactNode;
}) {
  const heroRef = useRef<HTMLDivElement>(null);
  const spotlightRef = useRef<HTMLDivElement>(null);
  const [activeIndex, setActiveIndex] = useState(0);
  const active = LANDING_DOMAINS[activeIndex];

  function handleMouseMove(e: React.MouseEvent<HTMLDivElement>) {
    const bounds = heroRef.current?.getBoundingClientRect();
    if (!bounds || !spotlightRef.current) return;
    const x = ((e.clientX - bounds.left) / bounds.width) * 100;
    const y = ((e.clientY - bounds.top) / bounds.height) * 100;
    spotlightRef.current.style.setProperty("--spot-x", `${x}%`);
    spotlightRef.current.style.setProperty("--spot-y", `${y}%`);
  }

  return (
    <div
      ref={heroRef}
      onMouseMove={handleMouseMove}
      className="relative min-h-screen w-full overflow-hidden bg-(--color-ink)"
    >
      {/* Cursor-reactive spotlight, replaces the old particle glow with a cheap CSS equivalent */}
      <div
        ref={spotlightRef}
        className="pointer-events-none absolute inset-0 transition-opacity duration-300"
        style={
          {
            "--spot-x": "50%",
            "--spot-y": "35%",
            background:
              "radial-gradient(600px circle at var(--spot-x) var(--spot-y), color-mix(in srgb, var(--color-accent-secondary) 18%, transparent), transparent 70%)",
          } as React.CSSProperties
        }
      />
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_center,_transparent_0%,_rgba(0,0,0,0.5)_100%)]" />

      <div className="relative z-10 mx-auto flex min-h-screen max-w-6xl flex-col items-center justify-center px-6 py-28 text-center">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
        >
          {children}
        </motion.div>

        {/* Interactive domain picker — swap tabs to preview what the AI Curator actually surfaces */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.15, ease: [0.16, 1, 0.3, 1] }}
          className="mt-14 w-full max-w-3xl"
        >
          <p className="mb-4 text-xs font-medium uppercase tracking-[0.3em] text-white/40">
            Try a domain
          </p>
          <div className="flex flex-wrap items-center justify-center gap-2">
            {LANDING_DOMAINS.map((domain, i) => {
              const isActive = i === activeIndex;
              return (
                <button
                  key={domain.name}
                  onClick={() => setActiveIndex(i)}
                  className="relative rounded-full px-4 py-2 text-[13px] font-medium transition-colors"
                  style={{
                    color: isActive ? "#0d0d0d" : "rgba(255,255,255,0.7)",
                  }}
                >
                  {isActive && (
                    <motion.span
                      layoutId="domain-pill"
                      className="absolute inset-0 rounded-full"
                      style={{ background: domain.color }}
                      transition={{ type: "spring", stiffness: 350, damping: 30 }}
                    />
                  )}
                  <span className="relative flex items-center gap-1.5">
                    <span aria-hidden>{domain.icon}</span>
                    {domain.name}
                  </span>
                </button>
              );
            })}
          </div>

          <AnimatePresence mode="wait">
            <motion.div
              key={active.name}
              initial={{ opacity: 0, y: 12, scale: 0.98 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -8, scale: 0.98 }}
              transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
              className="mt-6 overflow-hidden rounded-2xl bg-(--color-bg-offwhite) text-left shadow-2xl"
            >
              <div className="h-1.5 w-full" style={{ background: active.color }} />
              <div className="flex flex-col gap-4 p-6 sm:flex-row sm:items-center">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span
                      className="rounded-full px-2.5 py-0.5 text-[11px] font-semibold text-white"
                      style={{ background: active.color }}
                    >
                      {active.name}
                    </span>
                    <span className="text-[11px] text-(--color-text-tertiary)">
                      {active.duration}
                    </span>
                  </div>
                  <p className="mt-2.5 text-[13px] text-(--color-text-secondary)">
                    {active.blurb}
                  </p>
                  <p className="mt-2 text-[15px] font-semibold leading-snug text-(--color-ink)">
                    {active.sample}
                  </p>
                </div>
                <span
                  className="hidden shrink-0 items-center justify-center rounded-xl text-2xl sm:flex"
                  style={{
                    width: 56,
                    height: 56,
                    background: `color-mix(in srgb, ${active.color} 14%, transparent)`,
                  }}
                  aria-hidden
                >
                  {active.icon}
                </span>
              </div>
            </motion.div>
          </AnimatePresence>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3, ease: [0.16, 1, 0.3, 1] }}
          className="mt-10 flex flex-wrap items-center justify-center gap-4"
        >
          <MagneticButton
            href="/onboarding"
            className="inline-block rounded-full bg-(--color-bg-offwhite) px-7 py-3.5 text-[15px] font-medium text-(--color-ink) transition-transform hover:-translate-y-0.5"
          >
            Start Here
          </MagneticButton>
          <MagneticButton
            href="/onboarding"
            className="inline-block rounded-full border border-white/30 px-7 py-3.5 text-[15px] font-medium text-white transition-colors hover:bg-white/10"
          >
            I want to be better
          </MagneticButton>
        </motion.div>
      </div>
    </div>
  );
}
