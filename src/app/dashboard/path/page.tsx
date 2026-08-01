"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useIdentityStore } from "@/lib/store/identity.store";
import type { Goal } from "@/lib/api";

const DOMAIN_COLORS: Record<string, string> = {
  Creativity: "#F4A261",
  Mindset: "#5A4FF3",
  Health: "#00C9A7",
  Knowledge: "#3B82F6",
  Career: "#8B5CF6",
  Relationships: "#EC4899",
  Finance: "#22C55E",
  Purpose: "#F59E0B",
};

export default function PathPage() {
  const userId = useIdentityStore((s) => s.userId);
  const [goals, setGoals] = useState<Goal[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!userId) return;
    api.getGoals(userId)
      .then(setGoals)
      .finally(() => setLoading(false));
  }, [userId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <span className="animate-pulse text-(--color-text-tertiary)">Loading path…</span>
      </div>
    );
  }

  return (
    <div className="max-w-5xl space-y-10">
      <div>
        <p className="text-[13px] uppercase tracking-widest text-(--color-text-tertiary)">
          Your growth journey
        </p>
        <h1 className="mt-1 text-3xl font-bold tracking-tight text-(--color-ink)">My Path</h1>
      </div>

      {goals.length === 0 ? (
        <div className="flex items-center justify-center rounded-2xl border border-dashed border-(--color-border) py-24 text-center">
          <div>
            <p className="text-(--color-text-secondary)">No path started yet</p>
            <p className="mt-1 text-[13px] text-(--color-text-tertiary)">
              Complete onboarding to set your goals
            </p>
          </div>
        </div>
      ) : (
        <>
          {/* Journey timeline */}
          <div className="relative">
            {/* Connector line */}
            <div className="absolute left-6 top-8 bottom-8 w-0.5 bg-(--color-border)" />

            <div className="space-y-6">
              {/* Start node */}
              <div className="flex items-center gap-4">
                <div className="relative z-10 flex h-12 w-12 items-center justify-center rounded-full border-2 border-(--color-ink) bg-white text-[11px] font-bold text-(--color-ink)">
                  NOW
                </div>
                <div>
                  <p className="text-[15px] font-semibold text-(--color-ink)">Current Self</p>
                  <p className="text-[13px] text-(--color-text-tertiary)">Where you are today</p>
                </div>
              </div>

              {/* Goal milestones */}
              {goals.map((goal, i) => {
                const color = DOMAIN_COLORS[goal.domain] ?? "#8a8a8a";
                const pct = Math.round(goal.progress * 100);
                return (
                  <div key={goal.id} className="flex items-start gap-4">
                    <div
                      className="relative z-10 flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full text-white text-[11px] font-bold"
                      style={{ background: color }}
                    >
                      {i + 1}
                    </div>
                    <div className="flex-1 rounded-2xl border border-(--color-border) bg-white p-5">
                      <div className="flex items-center justify-between">
                        <div>
                          <span
                            className="text-[11px] font-semibold uppercase tracking-wider"
                            style={{ color }}
                          >
                            {goal.domain}
                          </span>
                          <p className="mt-0.5 text-[16px] font-semibold text-(--color-ink)">{goal.title}</p>
                          <p className="text-[12px] text-(--color-text-tertiary)">{goal.timeline}</p>
                        </div>
                        <div className="text-right">
                          <p className="text-2xl font-bold" style={{ color }}>{pct}%</p>
                          <p className="text-[11px] text-(--color-text-tertiary)">complete</p>
                        </div>
                      </div>
                      <div className="mt-4 h-2 w-full overflow-hidden rounded-full bg-(--color-border)">
                        <div
                          className="h-full rounded-full transition-all duration-700"
                          style={{ width: `${pct}%`, background: color }}
                        />
                      </div>
                    </div>
                  </div>
                );
              })}

              {/* End node */}
              <div className="flex items-center gap-4">
                <div className="relative z-10 flex h-12 w-12 items-center justify-center rounded-full border-2 border-dashed border-(--color-accent-secondary) bg-(--color-bg-offwhite) text-[11px] font-bold text-(--color-accent-secondary)">
                  IAM
                </div>
                <div>
                  <p className="text-[15px] font-semibold text-(--color-ink)">Imagined Self</p>
                  <p className="text-[13px] text-(--color-text-tertiary)">Who you are becoming</p>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
