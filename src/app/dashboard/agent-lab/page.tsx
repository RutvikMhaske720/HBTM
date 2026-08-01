"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useIdentityStore } from "@/lib/store/identity.store";
import type { AgentRun } from "@/lib/api";

const AGENT_COLORS: Record<string, string> = {
  "Memory Agent": "#6E5AA0",
  "Identity Agent": "#5E8F5A",
  "Goal Agent": "#2F6F6B",
  "Content Retrieval Agent": "#3E5E8C",
  "Recommendation Agent": "#C97A3D",
  "Safety Agent": "#A8497A",
  "Evaluation Agent": "#9C7A3A",
  "Human Approval": "#8a7a5e",
  "Output": "#7A8C4A",
  "Notification Agent": "#4d7a72",
  Runner: "#9c4a3c",
};

function StatusBadge({ status }: { status: string }) {
  const config: Record<string, { bg: string; text: string }> = {
    success: { bg: "bg-(--color-status-success-bg)", text: "text-(--color-status-success-text)" },
    completed: { bg: "bg-(--color-status-success-bg)", text: "text-(--color-status-success-text)" },
    error: { bg: "bg-(--color-status-error-bg)", text: "text-(--color-status-error-text)" },
    failed: { bg: "bg-(--color-status-error-bg)", text: "text-(--color-status-error-text)" },
    running: { bg: "bg-(--color-status-running-bg)", text: "text-(--color-status-running-text)" },
    skipped: { bg: "bg-(--color-status-neutral-bg)", text: "text-(--color-status-neutral-text)" },
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

  // Live trace: while the selected run is still going, stream its steps in
  // over SSE instead of waiting for a final one-shot fetch.
  useEffect(() => {
    if (!selectedRun || selectedRun.status !== "running") return;
    const runId = selectedRun.id;
    const source = new EventSource(api.agentStreamUrl(runId));

    source.onmessage = (event) => {
      const payload = JSON.parse(event.data);
      if (payload.type === "run_complete") {
        source.close();
        if (userId) {
          api.getAgentRuns(userId).then((r) => {
            setRuns(r);
            setSelectedRun((prev) => (prev && prev.id === runId ? r.find((x) => x.id === runId) ?? prev : prev));
          });
        }
        return;
      }
      setSelectedRun((prev) => (prev && prev.id === runId ? { ...prev, steps: [...prev.steps, payload] } : prev));
    };

    source.onerror = () => source.close();
    return () => source.close();
  }, [selectedRun?.id, selectedRun?.status, userId]);

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
                className={`w-full border-b border-(--color-border-subtle) px-5 py-3.5 text-left transition-colors hover:bg-(--color-surface) ${
                  selectedRun?.id === run.id ? "bg-(--color-surface)" : ""
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
        <div className="flex-1 overflow-y-auto rounded-2xl border border-(--color-border) bg-(--color-surface) p-5 font-mono text-[13px]">
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
                        <pre className="mt-2 overflow-x-auto rounded-lg bg-black/30 p-3 text-[11px] text-(--color-status-running-text)">
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
