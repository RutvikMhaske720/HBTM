"use client";

import { useEffect } from "react";
import { useIdentityStore } from "@/lib/store/identity.store";
import { useAgentStore } from "@/lib/store/agent.store";
import { api } from "@/lib/api";
import { useRouter } from "next/navigation";
import { supabase } from "@/lib/supabase";

const STATUS_DOT: Record<string, string> = {
  idle: "bg-(--color-text-tertiary)",
  running: "bg-(--color-accent-secondary) animate-pulse",
  completed: "bg-(--color-accent-tertiary)",
  failed: "bg-(--color-accent-focus)",
};

const STATUS_LABEL: Record<string, string> = {
  idle: "Idle",
  running: "Thinking…",
  completed: "Active",
  failed: "Error",
};

export default function TopNav() {
  const profile = useIdentityStore((s) => s.profile);
  const userId = useIdentityStore((s) => s.userId);
  const agentStatus = useAgentStore((s) => s.status);
  const confidenceScore = useAgentStore((s) => s.confidenceScore);
  const setAgentStatus = useAgentStore((s) => s.setAgentStatus);
  const setRunId = useAgentStore((s) => s.setRunId);
  const setConfidence = useAgentStore((s) => s.setConfidence);
  const clearIdentity = useIdentityStore((s) => s.clear);
  const router = useRouter();

  // Poll agent status every 5s
  useEffect(() => {
    if (!userId) return;
    const poll = async () => {
      try {
        const status = await api.getAgentStatus(userId);
        setAgentStatus(status.status as "idle" | "running" | "completed" | "failed");
        if (status.run_id) setRunId(status.run_id);
        if (status.confidence_score !== null && status.confidence_score !== undefined) {
          setConfidence(status.confidence_score);
        }
      } catch {
        // silent
      }
    };
    poll();
    const interval = setInterval(poll, 5000);
    return () => clearInterval(interval);
  }, [userId, setAgentStatus, setRunId, setConfidence]);

  const confidencePct = confidenceScore !== null ? Math.round(confidenceScore * 100) : null;
  const confidenceLabel =
    confidencePct === null
      ? null
      : confidencePct < 60
        ? `Still learning about you · ${confidencePct}%`
        : `Dialed in · ${confidencePct}%`;

  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening";
  const name = profile?.name || "there";

  return (
    <header className="flex h-16 items-center justify-between border-b border-(--color-border) bg-(--color-bg-primary) px-6 lg:px-10">
      <p className="text-[15px] font-medium text-(--color-ink)">
        {greeting}, <span className="text-(--color-text-secondary)">{name}</span>
      </p>

      <div className="flex items-center gap-5">
        {/* Agent status chip */}
        <div
          className="flex items-center gap-2 rounded-full border border-(--color-border) px-3 py-1.5"
          title={confidenceLabel ?? undefined}
        >
          <span className={`h-2 w-2 rounded-full ${STATUS_DOT[agentStatus] ?? STATUS_DOT.idle}`} />
          <span className="text-[12px] font-medium text-(--color-text-secondary)">
            Curator {STATUS_LABEL[agentStatus] ?? "Idle"}
          </span>
          {confidenceLabel && (
            <>
              <span className="h-3 w-px bg-(--color-border)" />
              <span className="text-[11px] text-(--color-text-tertiary)">{confidenceLabel}</span>
            </>
          )}
        </div>

        {/* User avatar */}
        <button onClick={() => void supabase.auth.signOut().then(() => { clearIdentity(); router.replace("/auth"); })} title="Sign out" className="flex h-8 w-8 items-center justify-center rounded-full bg-(--color-accent-secondary) text-[13px] font-bold text-(--color-text-inverse)">
          {name.charAt(0).toUpperCase()}
        </button>
      </div>
    </header>
  );
}
