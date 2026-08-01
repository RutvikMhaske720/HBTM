"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { useIdentityStore } from "@/lib/store/identity.store";
import type { Recommendation } from "@/lib/api";

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

const CONTENT_TYPE_EMOJI: Record<string, string> = {
  Film: "🎬",
  Music: "🎵",
  Art: "🎨",
  Animation: "✨",
  Editorial: "📰",
  Print: "📚",
  Podcast: "🎙️",
};

interface Props {
  rec: Recommendation;
  onFeedback?: (type: string) => void;
}

export default function RecommendationCard({ rec, onFeedback }: Props) {
  const [hovered, setHovered] = useState(false);
  const [showWhy, setShowWhy] = useState(false);
  const [feedbackSent, setFeedbackSent] = useState<string | null>(null);
  const userId = useIdentityStore((s) => s.userId);

  const domainColor = DOMAIN_COLORS[rec.domain] ?? "#8a8a8a";
  const emoji = CONTENT_TYPE_EMOJI[rec.content_type] ?? "📄";
  const growthPct = Math.round(rec.growth_potential_score * 100);

  async function handleFeedback(type: string) {
    setFeedbackSent(type);
    onFeedback?.(type);
    if (userId) {
      try {
        await api.submitFeedback(userId, rec.id, type);
      } catch {
        // silent
      }
    }
  }

  return (
    <div
      className={`group relative flex min-w-[220px] flex-col rounded-2xl border bg-(--color-surface) transition-all duration-200 ${
        hovered ? "border-(--color-ink) shadow-lg -translate-y-1" : "border-(--color-border)"
      }`}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      {/* Top color band */}
      <div
        className="h-2 w-full rounded-t-2xl"
        style={{ background: domainColor }}
      />

      <div className="flex flex-1 flex-col p-4">
        {/* Badges row */}
        <div className="mb-3 flex items-center gap-2">
          <span
            className="rounded-full px-2 py-0.5 text-[10px] font-semibold text-white"
            style={{ background: domainColor }}
          >
            {rec.domain}
          </span>
          <span className="rounded-full border border-(--color-border) px-2 py-0.5 text-[10px] text-(--color-text-tertiary)">
            {emoji} {rec.content_type}
          </span>
          {rec.source !== "internal" && (
            <span className="rounded-full border border-(--color-border) px-2 py-0.5 text-[10px] text-(--color-text-tertiary)">
              {rec.source}
            </span>
          )}
        </div>

        {/* Title */}
        <p className="flex-1 text-[15px] font-semibold leading-snug text-(--color-ink)">
          {rec.title}
        </p>

        {/* Meta */}
        <div className="mt-2 flex items-center gap-3 text-[12px] text-(--color-text-tertiary)">
          <span>{rec.duration_minutes}m</span>
          <span>·</span>
          <span>{rec.difficulty}</span>
          <span>·</span>
          <span className="font-medium" style={{ color: domainColor }}>
            {growthPct}% growth
          </span>
        </div>

        {/* Why recommended */}
        <button
          onClick={() => setShowWhy((v) => !v)}
          className="mt-3 text-left text-[11px] text-(--color-accent-secondary) hover:underline"
        >
          ✦ {showWhy ? "Hide reason" : "Why this?"}
        </button>

        {showWhy && (
          <p className="mt-1.5 rounded-lg bg-(--color-bg-offwhite) p-2.5 text-[12px] leading-relaxed text-(--color-text-secondary)">
            {rec.why_recommended}
          </p>
        )}

        {/* Action buttons */}
        {feedbackSent ? (
          <p className="mt-3 text-[12px] text-(--color-text-tertiary)">
            Feedback recorded ✓
          </p>
        ) : (
          <div className="mt-3 flex items-center gap-2">
            <button
              onClick={() => handleFeedback("thumbs_up")}
              className="flex-1 rounded-lg border border-(--color-border) py-1.5 text-[12px] font-medium text-(--color-ink) hover:bg-(--color-bg-offwhite)"
            >
              👍 Great
            </button>
            <button
              onClick={() => handleFeedback("done")}
              className="flex-1 rounded-lg border border-(--color-border) py-1.5 text-[12px] font-medium text-(--color-ink) hover:bg-(--color-bg-offwhite)"
            >
              ✓ Done
            </button>
            <button
              onClick={() => handleFeedback("not_for_me")}
              className="rounded-lg border border-(--color-border) px-2.5 py-1.5 text-[12px] text-(--color-text-tertiary) hover:border-(--color-accent-focus) hover:text-(--color-accent-focus)"
              title="Not for me"
            >
              ✕
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
