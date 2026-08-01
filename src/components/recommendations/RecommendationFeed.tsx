"use client";

import { useEffect, useRef } from "react";
import type { Recommendation } from "@/lib/api";
import RecommendationCard from "./RecommendationCard";
import { useRecommendationsStore } from "@/lib/store/recommendations.store";

interface Props {
  recommendations: Recommendation[];
  onFeedback?: (contentId: string, type: string) => void;
}

function SkeletonCard() {
  return (
    <div className="min-w-[220px] animate-pulse rounded-2xl border border-(--color-border) bg-(--color-surface)">
      <div className="h-2 w-full rounded-t-2xl bg-(--color-border)" />
      <div className="p-4 space-y-3">
        <div className="h-3 w-16 rounded-full bg-(--color-border)" />
        <div className="h-4 w-full rounded bg-(--color-border)" />
        <div className="h-4 w-3/4 rounded bg-(--color-border)" />
        <div className="h-3 w-24 rounded bg-(--color-border)" />
      </div>
    </div>
  );
}

export default function RecommendationFeed({ recommendations, onFeedback }: Props) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const isLoading = useRecommendationsStore((s) => s.isLoading);
  const addFeedback = useRecommendationsStore((s) => s.addFeedback);

  function handleFeedback(contentId: string, type: string) {
    addFeedback(contentId, type);
    onFeedback?.(contentId, type);
  }

  if (isLoading) {
    return (
      <div className="flex gap-4 overflow-x-auto pb-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
    );
  }

  if (!recommendations.length) {
    return (
      <div className="flex items-center justify-center rounded-2xl border border-dashed border-(--color-border) py-16 text-center">
        <div>
          <p className="text-(--color-text-secondary)">No recommendations yet</p>
          <p className="mt-1 text-[13px] text-(--color-text-tertiary)">Your curator is warming up…</p>
        </div>
      </div>
    );
  }

  return (
    <div ref={scrollRef} className="flex gap-4 overflow-x-auto pb-3 scrollbar-thin">
      {recommendations.map((rec) => (
        <RecommendationCard
          key={rec.id}
          rec={rec}
          onFeedback={(type) => handleFeedback(rec.id, type)}
        />
      ))}
    </div>
  );
}
