"use client";
import { create } from "zustand";

interface AgentStep {
  agent_name: string;
  status: string;
  duration_ms: number;
  detail: Record<string, unknown>;
}

type AgentStatus = "idle" | "running" | "completed" | "failed";

interface AgentState {
  status: AgentStatus;
  currentRunId: string | null;
  stepLog: AgentStep[];
  confidenceScore: number | null;
  setAgentStatus: (status: AgentStatus) => void;
  setRunId: (id: string) => void;
  appendStep: (step: AgentStep) => void;
  resetRun: () => void;
  setConfidence: (score: number) => void;
}

export const useAgentStore = create<AgentState>()((set) => ({
  status: "idle",
  currentRunId: null,
  stepLog: [],
  confidenceScore: null,
  setAgentStatus: (status) => set({ status }),
  setRunId: (id) => set({ currentRunId: id }),
  appendStep: (step) => set((s) => ({ stepLog: [...s.stepLog, step] })),
  resetRun: () => set({ status: "idle", stepLog: [], currentRunId: null, confidenceScore: null }),
  setConfidence: (score) => set({ confidenceScore: score }),
}));
