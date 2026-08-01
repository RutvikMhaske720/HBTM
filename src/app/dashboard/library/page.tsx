"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { ContentItem } from "@/lib/api";

const DOMAIN_COLORS: Record<string, string> = {
  Creativity: "#C97A3D",
  Mindset: "#6E5AA0",
  Health: "#5E8F5A",
  Knowledge: "#3E5E8C",
  Career: "#9C7A3A",
  Relationships: "#A8497A",
  Finance: "#7A8C4A",
  Purpose: "#2F6F6B",
};

const DOMAINS = ["All", "Creativity", "Mindset", "Health", "Knowledge", "Career", "Relationships", "Finance", "Purpose"];
const TYPES = ["All", "Film", "Music", "Art", "Animation", "Editorial", "Print", "Podcast"];

export default function LibraryPage() {
  const [items, setItems] = useState<ContentItem[]>([]);
  const [domain, setDomain] = useState("All");
  const [contentType, setContentType] = useState("All");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api.getContent({
      domain: domain !== "All" ? domain : undefined,
      content_type: contentType !== "All" ? contentType : undefined,
      limit: 100,
    })
      .then(setItems)
      .finally(() => setLoading(false));
  }, [domain, contentType]);

  return (
    <div className="max-w-6xl space-y-8">
      <div>
        <p className="text-[13px] uppercase tracking-widest text-(--color-text-tertiary)">
          IABTM curated
        </p>
        <h1 className="mt-1 text-3xl font-bold tracking-tight text-(--color-ink)">
          Media Library
        </h1>
        <p className="mt-1 text-[15px] text-(--color-text-secondary)">
          {items.length} items across all growth domains
        </p>
      </div>

      {/* Filters */}
      <div className="space-y-3">
        <div className="flex flex-wrap gap-2">
          <span className="self-center text-[12px] font-medium text-(--color-text-tertiary) w-14">Domain</span>
          {DOMAINS.map((d) => (
            <button
              key={d}
              onClick={() => setDomain(d)}
              className={`rounded-full px-3 py-1.5 text-[13px] font-medium transition-colors ${
                domain === d
                  ? "bg-(--color-accent-secondary) text-(--color-text-inverse)"
                  : "border border-(--color-border) text-(--color-ink) hover:bg-(--color-bg-offwhite)"
              }`}
            >
              {d}
            </button>
          ))}
        </div>
        <div className="flex flex-wrap gap-2">
          <span className="self-center text-[12px] font-medium text-(--color-text-tertiary) w-14">Type</span>
          {TYPES.map((t) => (
            <button
              key={t}
              onClick={() => setContentType(t)}
              className={`rounded-full px-3 py-1.5 text-[13px] font-medium transition-colors ${
                contentType === t
                  ? "bg-(--color-accent-secondary) text-(--color-text-inverse)"
                  : "border border-(--color-border) text-(--color-ink) hover:bg-(--color-bg-offwhite)"
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      {/* Grid */}
      {loading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="animate-pulse rounded-2xl border border-(--color-border) bg-(--color-surface) p-5 space-y-3">
              <div className="h-3 w-16 rounded-full bg-(--color-border)" />
              <div className="h-4 w-full rounded bg-(--color-border)" />
              <div className="h-3 w-24 rounded bg-(--color-border)" />
            </div>
          ))}
        </div>
      ) : items.length === 0 ? (
        <div className="flex items-center justify-center py-24 text-center">
          <p className="text-(--color-text-secondary)">No results — try a different filter</p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {items.map((item) => {
            const color = DOMAIN_COLORS[item.domain] ?? "#8a8a8a";
            const growthPct = Math.round(item.growth_potential_score * 100);
            return (
              <div
                key={item.id}
                className="group flex flex-col rounded-2xl border border-(--color-border) bg-(--color-surface) p-5 transition-all hover:-translate-y-0.5 hover:shadow-md"
              >
                {/* Top color band */}
                <div className="mb-4 h-1 w-12 rounded-full" style={{ background: color }} />

                <div className="flex items-center gap-2 text-[11px]">
                  <span
                    className="rounded-full px-2 py-0.5 font-semibold text-white"
                    style={{ background: color }}
                  >
                    {item.domain}
                  </span>
                  <span className="text-(--color-text-tertiary)">{item.content_type}</span>
                </div>

                <p className="mt-2 flex-1 text-[15px] font-semibold leading-snug text-(--color-ink)">
                  {item.title}
                </p>

                <p className="mt-2 line-clamp-2 text-[13px] leading-relaxed text-(--color-text-secondary)">
                  {item.description}
                </p>

                <div className="mt-4 flex items-center justify-between text-[12px] text-(--color-text-tertiary)">
                  <span>{item.duration_minutes}m · {item.difficulty}</span>
                  <span className="font-medium" style={{ color }}>{growthPct}% growth</span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
