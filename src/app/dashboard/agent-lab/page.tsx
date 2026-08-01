"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useIdentityStore } from "@/lib/store/identity.store";
import type { AgentRun } from "@/lib/api";

const AGENT_COLORS: Record<string, string> = {
  "Memory Agent": "#5A4FF3",
  "Identity Agent": "#00C9A7",
  "Goal Agent": "#F59E0B",
  "Content Retrieval Agent": "#3B82F6",
  "Recommendation Agent": "#F4A261",
  "Safety Agent": "#EC4899",
  "Evaluation Agent": "#8B5CF6",
  "Human Approval": "#6b7280",
  "Output": "#22C55E",
  "Notification Agent": "#14b8a6",
  Runner: "#ef4444",
};

function StatusBadge({ status }: { status: string }) {
  const config: Record<string, { bg: string; text: string }> = {
    success: { bg: "bg-emerald-100", text: "text-emerald-700" },
    completed: { bg: "bg-emerald-100", text: "text-emerald-700" },
    error: { bg: "bg-red-100", text: "text-red-700" },
    failed: { bg: "bg-red-100", text: "text-red-700" },
    running: { bg: "bg-violet-100", text: "text-violet-700" },
    skipped: { bg: "bg-gray-100", text: "text-gray-600" },
  };
  const s = config[status] ?? config.skipped;
  return (
    <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${s.bg} ${s.text}`}>
      {status}
    </span>
  );
}

export default function AgentLabPage() {
  const userId = useIdentityStore((s) => s.userId);
  const [runs, setRuns] = useState<AgentRun[]>([]);
  const [selectedRun, setSelectedRun] = useState<AgentRun | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!userId) return;
    api.getAgentRuns(userId).then((r) => {
      setRuns(r);
      if (r.length > 0) setSelectedRun(r[0]);
    }).finally(() => setLoading(false));
  }, [userId]);

  const steps = selectedRun?.steps ?? [];
  const totalMs = steps.reduce((a, s) => a + s.duration_ms, 0);
  const successCount = steps.filter((s) => s.status === "success").length;

  return (
    <div className="flex h-[calc(100vh-8rem)] gap-5">
      {/* Left: Run list */}
      <div className="flex w-64 flex-shrink-0 flex-col rounded-2xl border border-(--color-border) bg-(--color-bg-offwhite) overflow-hidden">
        <div className="border-b border-(--color-border) px-5 py-4">
          <h2 className="text-[13px] font-semibold uppercase tracking-wider text-(--color-text-tertiary)">
            Run History
          </h2>
        </div>
        <div className="flex-1 overflow-y-auto">
          {loading ? (
            <div className="p-5 text-[13px] text-(--color-text-tertiary)">Loading…</div>
          ) : runs.length === 0 ? (
            <div className="p-5 text-[13px] text-(--color-text-tertiary)">
              No runs yet. Trigger one from the dashboard.
            </div>
          ) : (
            runs.map((run) => (
              <button
                key={run.id}
                onClick={() => setSelectedRun(run)}
                className={`w-full border-b border-(--color-border-subtle) px-5 py-3.5 text-left transition-colors hover:bg-white ${
                  selectedRun?.id === run.id ? "bg-white" : ""
                }`}
              >
                <div className="flex items-center justify-between">
                  <StatusBadge status={run.status} />
                  <span className="text-[10px] text-(--color-text-tertiary)">
                    {run.confidence_score ? `${Math.round(run.confidence_score * 100)}% conf` : ""}
                  </span>
                </div>
                <p className="mt-1.5 text-[12px] font-medium text-(--color-ink)">
                  {run.trigger_type.replace("_", " ")}
                </p>
                <p className="mt-0.5 text-[11px] text-(--color-text-tertiary)">
                  {new Date(run.started_at).toLocaleString()}
                </p>
              </button>
            ))
          )}
        </div>
      </div>

      {/* Main: Trace viewer */}
      <div className="flex flex-1 flex-col gap-5 overflow-hidden">
        {/* Metrics bar */}
        {selectedRun && (
          <div className="grid grid-cols-4 gap-4">
            {[
              { label: "Total Time", value: `${totalMs}ms` },
              { label: "Steps", value: steps.length.toString() },
              { label: "Success", value: successCount.toString() },
              { label: "Confidence", value: selectedRun.confidence_score ? `${Math.round(selectedRun.confidence_score * 100)}%` : "—" },
            ].map((m) => (
              <div key={m.label} className="rounded-xl border border-(--color-border) bg-(--color-bg-offwhite) p-4">
                <p className="text-xl font-bold text-(--color-ink)">{m.value}</p>
                <p className="mt-0.5 text-[11px] text-(--color-text-tertiary)">{m.label}</p>
              </div>
            ))}
          </div>
        )}

        {/* Step trace */}
        <div className="flex-1 overflow-y-auto rounded-2xl border border-(--color-border) bg-(--color-ink) p-5 font-mono text-[13px]">
          {!selectedRun ? (
            <p className="text-(--color-text-tertiary)">Select a run to see its trace.</p>
          ) : steps.length === 0 ? (
            <p className="text-(--color-text-tertiary)">No steps recorded for this run.</p>
          ) : (
            <div className="space-y-3">
              {steps.map((step, i) => {
                const color = AGENT_COLORS[step.agent_name] ?? "#8a8a8a";
                return (
                  <div
                    key={i}
                    className="rounded-xl border border-white/10 bg-white/5 p-4"
                    style={{ borderLeftColor: color, borderLeftWidth: 3 }}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-white">[{step.agent_name}]</span>
                        <StatusBadge status={step.status} />
                      </div>
                      <span className="text-white/40">{step.duration_ms}ms</span>
                    </div>
                    {Object.keys(step.detail).length > 0 && (
                      <details className="mt-2">
                        <summary className="cursor-pointer text-white/60 hover:text-white/90">
                          Detail
                        </summary>
                        <pre className="mt-2 overflow-x-auto rounded-lg bg-black/30 p-3 text-[11px] text-emerald-300">
                          {JSON.stringify(step.detail, null, 2)}
                        </pre>
                      </details>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
