"use client";

import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import { useIdentityStore } from "@/lib/store/identity.store";
import type { IdentityGraph, IdentityNode } from "@/lib/api";

const NODE_COLORS: Record<string, string> = {
  archetype: "#6E5AA0",
  trait: "#5E8F5A",
  habit: "#C97A3D",
  skill: "#3E5E8C",
  value: "#A8497A",
};

const SVG_W = 900;
const SVG_H = 560;
const ME_HUB = { x: 190, y: 300 };
const IAM_HUB = { x: 710, y: 300 };
const ARC_SPREAD = 190;
const RADII = [116, 158, 202];

type LayoutNode = { node: IdentityNode; x: number; y: number };

function arcLayout(nodes: IdentityNode[], hub: { x: number; y: number }, centerAngle: number, spread: number): LayoutNode[] {
  const n = nodes.length;
  return nodes.map((node, i) => {
    const angle = n === 1 ? centerAngle : centerAngle - spread / 2 + (spread / (n - 1)) * i;
    const radius = RADII[i % RADII.length];
    const rad = (angle * Math.PI) / 180;
    return { node, x: hub.x + radius * Math.cos(rad), y: hub.y + radius * Math.sin(rad) };
  });
}

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

  const currentNodes = graph?.nodes.filter((n) => n.polarity === "current" && n.node_type !== "narrative") ?? [];
  const imaginedNodes = graph?.nodes.filter((n) => n.polarity === "imagined" && n.node_type !== "narrative") ?? [];
  const currentNarrative = graph?.nodes.find((n) => n.polarity === "current" && n.node_type === "narrative")?.label;
  const imaginedNarrative = graph?.nodes.find((n) => n.polarity === "imagined" && n.node_type === "narrative")?.label;

  const currentLayout = useMemo(() => arcLayout(currentNodes, ME_HUB, 180, ARC_SPREAD), [currentNodes]);
  const imaginedLayout = useMemo(() => arcLayout(imaginedNodes, IAM_HUB, 0, ARC_SPREAD), [imaginedNodes]);

  const allNodes = [...currentNodes, ...imaginedNodes];
  const avgWeight = allNodes.length > 0
    ? Math.round((allNodes.reduce((acc, n) => acc + n.weight, 0) / allNodes.length) * 100)
    : 0;

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <span className="animate-pulse text-(--color-text-tertiary)">Loading identity graph…</span>
      </div>
    );
  }

  return (
    <div className="max-w-6xl space-y-8">
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
          <div className="space-y-6">
            {/* Quick-read stats so the graph isn't the only signal */}
            <div className="grid grid-cols-3 gap-4">
              <div className="rounded-2xl border border-(--color-border) bg-(--color-bg-offwhite) p-4">
                <p className="text-2xl font-bold text-(--color-ink)">{currentNodes.length}</p>
                <p className="mt-0.5 text-[12px] text-(--color-text-tertiary)">Current-self traits</p>
              </div>
              <div className="rounded-2xl border border-(--color-border) bg-(--color-bg-offwhite) p-4">
                <p className="text-2xl font-bold text-(--color-ink)">{imaginedNodes.length}</p>
                <p className="mt-0.5 text-[12px] text-(--color-text-tertiary)">Imagined-self traits</p>
              </div>
              <div className="rounded-2xl border border-(--color-border) bg-(--color-bg-offwhite) p-4">
                <p className="text-2xl font-bold text-(--color-accent-secondary)">{avgWeight}%</p>
                <p className="mt-0.5 text-[12px] text-(--color-text-tertiary)">Avg. node weight</p>
              </div>
            </div>

            {/* Graph visualization — radial network: Me and I Am as hubs,
                traits as orbiting nodes, a "becoming" edge joins the two hubs */}
            <div className="rounded-2xl border border-(--color-border) bg-(--color-bg-offwhite) p-6">
              <svg
                viewBox={`-220 0 ${SVG_W + 440} ${SVG_H}`}
                className="w-full h-auto"
                role="img"
                aria-label="Identity graph: current-self traits fan left from a Me hub, imagined-self traits fan right from an I Am hub, joined by a becoming edge"
              >
                <defs>
                  <marker id="growth-arrow" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto">
                    <path d="M0,0 L8,4 L0,8 Z" fill="var(--color-accent-secondary)" />
                  </marker>
                </defs>

                {/* becoming edge */}
                <line
                  x1={ME_HUB.x + 34}
                  y1={ME_HUB.y}
                  x2={IAM_HUB.x - 36}
                  y2={IAM_HUB.y}
                  stroke="var(--color-accent-secondary)"
                  strokeWidth={2}
                  strokeDasharray="6 6"
                  markerEnd="url(#growth-arrow)"
                />
                <text
                  x={(ME_HUB.x + IAM_HUB.x) / 2}
                  y={ME_HUB.y - 14}
                  textAnchor="middle"
                  className="text-[11px] font-semibold uppercase tracking-wider"
                  style={{ fill: "var(--color-accent-secondary)" }}
                >
                  becoming
                </text>

                {/* connector lines */}
                {currentLayout.map(({ node, x, y }) => (
                  <line
                    key={`l-${node.id}`}
                    x1={ME_HUB.x}
                    y1={ME_HUB.y}
                    x2={x}
                    y2={y}
                    stroke={NODE_COLORS[node.node_type] ?? "#8a8a8a"}
                    strokeWidth={1.5}
                    opacity={0.2 + node.weight * 0.35}
                  />
                ))}
                {imaginedLayout.map(({ node, x, y }) => (
                  <line
                    key={`l-${node.id}`}
                    x1={IAM_HUB.x}
                    y1={IAM_HUB.y}
                    x2={x}
                    y2={y}
                    stroke={NODE_COLORS[node.node_type] ?? "#8a8a8a"}
                    strokeWidth={1.5}
                    opacity={0.2 + node.weight * 0.35}
                  />
                ))}

                {/* hubs */}
                <circle cx={ME_HUB.x} cy={ME_HUB.y} r={30} style={{ fill: "var(--color-surface-raised)", stroke: "var(--color-border)" }} strokeWidth={1.5} />
                <text x={ME_HUB.x} y={ME_HUB.y + 4} textAnchor="middle" className="text-[12px] font-bold" style={{ fill: "var(--color-ink)" }}>
                  ME
                </text>
                <circle cx={IAM_HUB.x} cy={IAM_HUB.y} r={30} style={{ fill: "var(--color-accent-secondary)" }} />
                <text x={IAM_HUB.x} y={IAM_HUB.y + 4} textAnchor="middle" className="text-[12px] font-bold" style={{ fill: "var(--color-text-inverse)" }}>
                  I AM
                </text>

                {/* current-self nodes */}
                {currentLayout.map(({ node, x, y }) => {
                  const color = NODE_COLORS[node.node_type] ?? "#8a8a8a";
                  const r = 6 + node.weight * 10;
                  const isSelected = selected?.id === node.id;
                  return (
                    <g key={node.id} onClick={() => setSelected(node)} className="cursor-pointer">
                      {isSelected && (
                        <circle cx={x} cy={y} r={r + 5} fill="none" style={{ stroke: "var(--color-ink)" }} strokeWidth={2} />
                      )}
                      <circle cx={x} cy={y} r={r} fill={color} opacity={0.55 + node.weight * 0.45} />
                      <text
                        x={x - r - 8}
                        y={y + 4}
                        textAnchor="end"
                        className="text-[12px] font-medium"
                        style={{ fill: "var(--color-ink)" }}
                      >
                        {node.label}
                      </text>
                    </g>
                  );
                })}

                {/* imagined-self nodes */}
                {imaginedLayout.map(({ node, x, y }) => {
                  const color = NODE_COLORS[node.node_type] ?? "#8a8a8a";
                  const r = 6 + node.weight * 10;
                  const isSelected = selected?.id === node.id;
                  return (
                    <g key={node.id} onClick={() => setSelected(node)} className="cursor-pointer">
                      {isSelected && (
                        <circle cx={x} cy={y} r={r + 5} fill="none" style={{ stroke: "var(--color-ink)" }} strokeWidth={2} />
                      )}
                      <circle cx={x} cy={y} r={r} fill={color} opacity={0.55 + node.weight * 0.45} />
                      <text
                        x={x + r + 8}
                        y={y + 4}
                        textAnchor="start"
                        className="text-[12px] font-medium"
                        style={{ fill: "var(--color-ink)" }}
                      >
                        {node.label}
                      </text>
                    </g>
                  );
                })}
              </svg>

              {/* Legend */}
              <div className="mt-4 flex flex-wrap gap-3 border-t border-(--color-border) pt-4">
                {Object.entries(NODE_COLORS).map(([type, color]) => (
                  <span key={type} className="flex items-center gap-1.5 text-[11px] text-(--color-text-tertiary)">
                    <span className="h-2.5 w-2.5 rounded-full" style={{ background: color }} />
                    {type}
                  </span>
                ))}
                <span className="ml-auto text-[11px] text-(--color-text-tertiary)">Bubble size = weight · click a node for detail</span>
              </div>
            </div>

            {/* In their own words — free text from onboarding, kept as prose
                rather than squeezed into a pill */}
            {(currentNarrative || imaginedNarrative) && (
              <div className="space-y-3">
                {currentNarrative && (
                  <p className="rounded-xl border border-(--color-border) bg-(--color-surface) p-3 text-[13px] italic leading-relaxed text-(--color-text-secondary)">
                    “{currentNarrative}”
                  </p>
                )}
                {imaginedNarrative && (
                  <p className="rounded-xl border border-(--color-border) bg-(--color-accent-secondary)/5 p-3 text-[13px] italic leading-relaxed text-(--color-text-secondary)">
                    “{imaginedNarrative}”
                  </p>
                )}
              </div>
            )}
          </div>

          {/* Node detail panel */}
          <div className="rounded-2xl border border-(--color-border) bg-(--color-surface) p-5">
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
