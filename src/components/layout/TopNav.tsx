"use client";

import { useEffect } from "react";
import { useIdentityStore } from "@/lib/store/identity.store";
import { useAgentStore } from "@/lib/store/agent.store";
import { api } from "@/lib/api";

const STATUS_DOT: Record<string, string> = {
  idle: "bg-(--color-text-tertiary)",
  running: "bg-(--color-accent-secondary) animate-pulse",
  completed: "bg-(--color-accent-tertiary)",
  failed: "bg-red-500",
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
  const setAgentStatus = useAgentStore((s) => s.setAgentStatus);
  const setRunId = useAgentStore((s) => s.setRunId);

  // Poll agent status every 5s
  useEffect(() => {
    if (!userId) return;
    const poll = async () => {
      try {
        const status = await api.getAgentStatus(userId);
        setAgentStatus(status.status as "idle" | "running" | "completed" | "failed");
        if (status.run_id) setRunId(status.run_id);
      } catch {
        // silent
      }
    };
    poll();
    const interval = setInterval(poll, 5000);
    return () => clearInterval(interval);
  }, [userId, setAgentStatus, setRunId]);

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
        <div className="flex items-center gap-2 rounded-full border border-(--color-border) px-3 py-1.5">
          <span className={`h-2 w-2 rounded-full ${STATUS_DOT[agentStatus] ?? STATUS_DOT.idle}`} />
          <span className="text-[12px] font-medium text-(--color-text-secondary)">
            Curator {STATUS_LABEL[agentStatus] ?? "Idle"}
          </span>
        </div>

        {/* User avatar */}
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-(--color-ink) text-[13px] font-bold text-white">
          {name.charAt(0).toUpperCase()}
        </div>
      </div>
    </header>
  );
}
