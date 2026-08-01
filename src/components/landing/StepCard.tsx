"use client";

import { motion } from "framer-motion";

export default function StepCard({
  index,
  title,
  body,
  accent,
}: {
  index: number;
  title: string;
  body: string;
  accent: string;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-80px" }}
      transition={{ duration: 0.5, delay: index * 0.12, ease: [0.16, 1, 0.3, 1] }}
      whileHover={{ y: -6 }}
      className="group rounded-2xl border border-(--color-border) bg-(--color-bg-offwhite) p-8 transition-shadow duration-300 hover:shadow-xl"
    >
      <span
        className="inline-flex h-9 w-9 items-center justify-center rounded-full text-[13px] font-semibold text-white transition-transform duration-300 group-hover:scale-110"
        style={{ background: accent }}
      >
        0{index + 1}
      </span>
      <h3 className="mt-4 text-xl font-semibold text-(--color-ink)">{title}</h3>
      <p className="mt-2 text-[15px] leading-relaxed text-(--color-text-secondary)">{body}</p>
    </motion.div>
  );
}
