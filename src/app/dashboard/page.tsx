"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useIdentityStore } from "@/lib/store/identity.store";
import { useRecommendationsStore } from "@/lib/store/recommendations.store";
import { useAgentStore } from "@/lib/store/agent.store";
import RecommendationFeed from "@/components/recommendations/RecommendationFeed";
import AmbientBackdrop from "@/components/AmbientBackdrop";
import type { Goal, Recommendation } from "@/lib/api";

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

export default function DashboardPage() {
  const userId = useIdentityStore((s) => s.userId);
  const profile = useIdentityStore((s) => s.profile);
  const { recommendations, setRecommendations, setLoading, isLoading } = useRecommendationsStore();
  const agentStatus = useAgentStore((s) => s.status);
  const [goals, setGoals] = useState<Goal[]>([]);
  const [feedbackCount, setFeedbackCount] = useState(0);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    if (!userId) return;
    setLoading(true);

    Promise.all([
      api.getRecommendations(userId),
      api.getGoals(userId),
      api.getFeedbackCount(userId),
    ])
      .then(([recs, g, feedback]) => {
        setRecommendations(recs);
        setGoals(g);
        setFeedbackCount(feedback.count);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [userId, setRecommendations, setLoading]);

  async function handleRefresh() {
    if (!userId) return;
    setRefreshing(true);
    try {
      await api.refreshRecommendations(userId);
      // Wait a bit for agent to run then fetch
      await new Promise((r) => setTimeout(r, 3000));
      const recs = await api.getRecommendations(userId);
      setRecommendations(recs);
    } catch (e) {
      console.error(e);
    } finally {
      setRefreshing(false);
    }
  }

  return (
    <div className="max-w-6xl space-y-10">
      {/* Header */}
      <div className="relative flex items-start justify-between overflow-hidden rounded-3xl border border-(--color-border) bg-(--color-surface-raised) px-8 py-10">
        <AmbientBackdrop />
        <div className="pointer-events-none absolute inset-0 bg-linear-to-b from-transparent to-(--color-bg-primary)/60" />
        <div className="relative z-10">
          <p className="text-[13px] uppercase tracking-widest text-white/50">
            AI-Curated Growth Feed
          </p>
          <h1 className="mt-1 text-3xl font-bold tracking-tight text-(--color-spotlight)">
            Your Dashboard
          </h1>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing || agentStatus === "running"}
          className="relative z-10 rounded-full border border-white/25 px-5 py-2.5 text-[14px] font-medium text-white hover:bg-white/10 disabled:opacity-40 transition-colors"
        >
          {refreshing ? "Refreshing…" : "↺ Refresh"}
        </button>
      </div>

      {/* Quick stats */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-5">
        {[
          { label: "Recommendations", value: recommendations.length.toString(), icon: "✦" },
          { label: "Active Goals", value: goals.length.toString(), icon: "◎" },
          { label: "Avg Growth Score", value: recommendations.length > 0 ? `${Math.round((recommendations.reduce((acc, r) => acc + r.growth_potential_score, 0) / recommendations.length) * 100)}%` : "—", icon: "↑" },
          { label: "Domains Covered", value: [...new Set(recommendations.map((r) => r.domain))].length.toString(), icon: "◈" },
          { label: "Feedback Given", value: feedbackCount.toString(), icon: "◆" },
        ].map((stat) => (
          <div
            key={stat.label}
            className="rounded-2xl border border-(--color-border) bg-(--color-bg-offwhite) p-5"
          >
            <span className="text-lg">{stat.icon}</span>
            <p className="mt-2 text-2xl font-bold text-(--color-ink)">{stat.value}</p>
            <p className="mt-0.5 text-[12px] text-(--color-text-tertiary)">{stat.label}</p>
          </div>
        ))}
      </div>

      {/* Curated Feed */}
      <section>
        <div className="mb-4 flex items-center gap-3">
          <h2 className="text-lg font-semibold text-(--color-ink)">For You Today</h2>
          <span className="inline-flex items-center gap-1.5 rounded-full bg-(--color-accent-secondary)/10 px-2.5 py-0.5 text-[11px] font-medium text-(--color-accent-secondary)">
            <span className="h-1.5 w-1.5 rounded-full bg-(--color-accent-secondary)" />
            AI Curated
          </span>
        </div>
        <RecommendationFeed
          recommendations={recommendations}
          onFeedback={() => setFeedbackCount((c) => c + 1)}
        />
      </section>

      {/* Active Goals */}
      {goals.length > 0 && (
        <section>
          <h2 className="mb-4 text-lg font-semibold text-(--color-ink)">Active Goals</h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {goals.map((goal) => {
              const color = DOMAIN_COLORS[goal.domain] ?? "#8a8a8a";
              const pct = Math.round(goal.progress * 100);
              return (
                <div
                  key={goal.id}
                  className="rounded-2xl border border-(--color-border) bg-(--color-surface) p-5"
                >
                  <div className="flex items-center gap-2">
                    <span
                      className="h-3 w-3 rounded-full"
                      style={{ background: color }}
                    />
                    <span
                      className="text-[11px] font-semibold uppercase tracking-wider"
                      style={{ color }}
                    >
                      {goal.domain}
                    </span>
                  </div>
                  <p className="mt-2 text-[15px] font-semibold text-(--color-ink)">{goal.title}</p>
                  <p className="mt-0.5 text-[12px] text-(--color-text-tertiary)">{goal.timeline}</p>
                  <div className="mt-4">
                    <div className="flex items-center justify-between text-[12px] text-(--color-text-tertiary)">
                      <span>Progress</span>
                      <span>{pct}%</span>
                    </div>
                    <div className="mt-1.5 h-1.5 w-full overflow-hidden rounded-full bg-(--color-border)">
                      <div
                        className="h-full rounded-full transition-all duration-700"
                        style={{ width: `${pct}%`, background: color }}
                      />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      )}
    </div>
  );
}
