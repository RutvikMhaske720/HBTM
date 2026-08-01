"use client";

import { useEffect, useRef, useState } from "react";
import { useInView, useMotionValue, useSpring } from "framer-motion";
import { LANDING_DOMAINS } from "@/lib/landingDomains";

function Counter({ to, suffix = "" }: { to: number; suffix?: string }) {
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true, margin: "-40px" });
  const motionVal = useMotionValue(0);
  const spring = useSpring(motionVal, { stiffness: 60, damping: 18 });
  const [display, setDisplay] = useState(0);

  useEffect(() => {
    if (inView) motionVal.set(to);
  }, [inView, to, motionVal]);

  useEffect(() => {
    return spring.on("change", (v) => setDisplay(Math.round(v)));
  }, [spring]);

  return (
    <span ref={ref}>
      {display}
      {suffix}
    </span>
  );
}

const FORMAT_COUNT = new Set(
  LANDING_DOMAINS.map((d) => d.duration.split(" · ")[1]),
).size;
const AVG_MINUTES = Math.round(
  LANDING_DOMAINS.reduce((sum, d) => sum + parseInt(d.duration, 10), 0) /
    LANDING_DOMAINS.length,
);

const STATS = [
  { value: LANDING_DOMAINS.length, label: "Growth domains tracked" },
  { value: FORMAT_COUNT, label: "Content formats curated" },
  { value: AVG_MINUTES, suffix: " min", label: "Average pick length" },
];

export default function StatsStrip() {
  return (
    <section className="border-y border-(--color-border) bg-(--color-bg-offwhite)">
      <div className="mx-auto grid max-w-6xl grid-cols-1 divide-y divide-(--color-border) sm:grid-cols-3 sm:divide-x sm:divide-y-0">
        {STATS.map((stat) => (
          <div key={stat.label} className="flex flex-col items-center gap-1 px-8 py-10 text-center">
            <span className="text-4xl font-extrabold tracking-tight text-(--color-ink)">
              <Counter to={stat.value} suffix={stat.suffix} />
            </span>
            <span className="text-[13px] text-(--color-text-tertiary)">{stat.label}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
