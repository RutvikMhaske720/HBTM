"use client";
import { create } from "zustand";
import type { Recommendation } from "@/lib/api";

interface RecommendationsState {
  recommendations: Recommendation[];
  isLoading: boolean;
  lastRefresh: string | null;
  setRecommendations: (recs: Recommendation[]) => void;
  setLoading: (v: boolean) => void;
  addFeedback: (contentId: string, type: string) => void;
}

export const useRecommendationsStore = create<RecommendationsState>()((set) => ({
  recommendations: [],
  isLoading: false,
  lastRefresh: null,
  setRecommendations: (recs) =>
    set({ recommendations: recs, lastRefresh: new Date().toISOString() }),
  setLoading: (v) => set({ isLoading: v }),
  addFeedback: (contentId, type) =>
    set((s) => ({
      // Optimistically remove dismissed/not-for-me items
      recommendations:
        type === "not_for_me" || type === "thumbs_down"
          ? s.recommendations.filter((r) => r.id !== contentId)
          : s.recommendations,
    })),
}));
