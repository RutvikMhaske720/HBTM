"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useIdentityStore } from "@/lib/store/identity.store";
import type { IdentityGraph, IdentityNode } from "@/lib/api";

const NODE_COLORS: Record<string, string> = {
  archetype: "#5A4FF3",
  trait: "#00C9A7",
  habit: "#F4A261",
  skill: "#3B82F6",
  value: "#EC4899",
};

const POLARITY_BG: Record<string, string> = {
  current: "#f7f5f0",
  imagined: "#eef2ff",
};

export default function IdentityPage() {
  const userId = useIdentityStore((s) => s.userId);
  const [graph, setGraph] = useState<IdentityGraph | null>(null);
  const [selected, setSelected] = useState<IdentityNode | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!userId) return;
    api.getIdentityGraph(userId)
      .then(setGraph)
      .finally(() => setLoading(false));
  }, [userId]);

  const currentNodes = graph?.nodes.filter((n) => n.polarity === "current") ?? [];
  const imaginedNodes = graph?.nodes.filter((n) => n.polarity === "imagined") ?? [];

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <span className="animate-pulse text-(--color-text-tertiary)">Loading identity graph…</span>
      </div>
    );
  }

  return (
    <div className="max-w-5xl space-y-8">
      <div>
        <p className="text-[13px] uppercase tracking-widest text-(--color-text-tertiary)">
          Living representation
        </p>
        <h1 className="mt-1 text-3xl font-bold tracking-tight text-(--color-ink)">
          Identity Graph
        </h1>
        <p className="mt-2 text-[15px] text-(--color-text-secondary)">
          {graph?.nodes.length ?? 0} nodes · Updated from your onboarding and interactions
        </p>
      </div>

      {!graph || graph.nodes.length === 0 ? (
        <div className="flex items-center justify-center rounded-2xl border border-dashed border-(--color-border) py-24 text-center">
          <p className="text-(--color-text-secondary)">
            Your identity graph is growing — keep interacting
          </p>
        </div>
      ) : (
        <div className="grid gap-6 lg:grid-cols-[1fr_280px]">
          {/* Graph visualization — bubble layout */}
          <div className="rounded-2xl border border-(--color-border) bg-(--color-bg-offwhite) p-6">
            <div className="grid gap-6 sm:grid-cols-2">
              {/* Current self column */}
              <div>
                <div className="mb-4 flex items-center gap-2">
                  <span className="flex h-7 w-16 items-center justify-center rounded-full bg-(--color-ink) text-[11px] font-bold text-white">
                    Me
                  </span>
                  <span className="text-[12px] text-(--color-text-tertiary)">Current self</span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {currentNodes.map((node) => {
                    const color = NODE_COLORS[node.node_type] ?? "#8a8a8a";
                    const size = Math.round(node.weight * 100);
                    return (
                      <button
                        key={node.id}
                        onClick={() => setSelected(node)}
                        className={`rounded-full px-3 py-1.5 text-[13px] font-medium text-white transition-transform hover:scale-105 ${
                          selected?.id === node.id ? "ring-2 ring-offset-1 ring-(--color-ink)" : ""
                        }`}
                        style={{ background: color, opacity: 0.6 + node.weight * 0.4 }}
                        title={`Weight: ${size}%`}
                      >
                        {node.label}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Imagined self column */}
              <div>
                <div className="mb-4 flex items-center gap-2">
                  <span className="flex h-7 w-16 items-center justify-center rounded-full bg-(--color-accent-secondary) text-[11px] font-bold text-white">
                    I Am
                  </span>
                  <span className="text-[12px] text-(--color-text-tertiary)">Imagined self</span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {imaginedNodes.map((node) => {
                    const color = NODE_COLORS[node.node_type] ?? "#5A4FF3";
                    return (
                      <button
                        key={node.id}
                        onClick={() => setSelected(node)}
                        className={`rounded-full px-3 py-1.5 text-[13px] font-medium text-white transition-transform hover:scale-105 ${
                          selected?.id === node.id ? "ring-2 ring-offset-1 ring-(--color-ink)" : ""
                        }`}
                        style={{ background: color, opacity: 0.6 + node.weight * 0.4 }}
                      >
                        {node.label}
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Legend */}
            <div className="mt-6 flex flex-wrap gap-3 border-t border-(--color-border) pt-4">
              {Object.entries(NODE_COLORS).map(([type, color]) => (
                <span key={type} className="flex items-center gap-1.5 text-[11px] text-(--color-text-tertiary)">
                  <span className="h-2.5 w-2.5 rounded-full" style={{ background: color }} />
                  {type}
                </span>
              ))}
            </div>
          </div>

          {/* Node detail panel */}
          <div className="rounded-2xl border border-(--color-border) bg-white p-5">
            {selected ? (
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-wider text-(--color-text-tertiary)">
                  Node Detail
                </p>
                <h3 className="mt-2 text-xl font-bold text-(--color-ink)">{selected.label}</h3>
                <div className="mt-4 space-y-3 text-[13px]">
                  <div className="flex justify-between">
                    <span className="text-(--color-text-tertiary)">Type</span>
                    <span
                      className="rounded-full px-2.5 py-0.5 text-[11px] font-semibold text-white"
                      style={{ background: NODE_COLORS[selected.node_type] ?? "#8a8a8a" }}
                    >
                      {selected.node_type}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-(--color-text-tertiary)">Polarity</span>
                    <span className="font-medium text-(--color-ink)">{selected.polarity}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-(--color-text-tertiary)">Source</span>
                    <span className="font-medium text-(--color-ink)">{selected.source.replace("_", " ")}</span>
                  </div>
                  <div>
                    <div className="flex items-center justify-between">
                      <span className="text-(--color-text-tertiary)">Weight</span>
                      <span className="font-bold text-(--color-ink)">{Math.round(selected.weight * 100)}%</span>
                    </div>
                    <div className="mt-1.5 h-2 w-full overflow-hidden rounded-full bg-(--color-border)">
                      <div
                        className="h-full rounded-full bg-(--color-accent-secondary)"
                        style={{ width: `${Math.round(selected.weight * 100)}%` }}
                      />
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex h-full items-center justify-center text-center">
                <p className="text-[13px] text-(--color-text-tertiary)">
                  Click any node to see details
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
