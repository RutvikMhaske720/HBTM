/**
 * Typed API client — all backend calls go through here.
 * Set NEXT_PUBLIC_API_URL in .env.local to point at the FastAPI server.
 */

export const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function req<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`API ${res.status}: ${text}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

// ─── Types ────────────────────────────────────────────────────────────────────

export interface OnboardingPayload {
  name: string;
  profile_name: string;
  email: string;
  phone: string;
  current_self: string[];
  imagined_self: string[];
  current_self_notes?: string;
  imagined_self_notes?: string;
  goals: string[];
  goal_domains: string[];
  timeline: string;
  learning_styles: string[];
  media_types: string[];
}

export interface OnboardingResponse {
  user_id: string;
  name: string;
}

export interface GoalSuggestion {
  domain: string;
  suggested_title: string;
}

export interface ScoreBreakdown {
  goal_alignment: number;
  identity_match: number;
  growth_potential: number;
  recency: number;
  feedback: number;
}

export interface Recommendation {
  id: string;
  title: string;
  content_type: string;
  domain: string;
  description: string;
  growth_potential_score: number;
  difficulty: string;
  duration_minutes: number;
  mood: string;
  source: string;
  url: string;
  why_recommended: string;
  score: number;
  score_breakdown: ScoreBreakdown | null;
  run_id: string | null;
}

export interface Goal {
  id: string;
  domain: string;
  title: string;
  timeline: string;
  progress: number;
  status: string;
  created_at: string;
}

export interface ContentItem {
  id: string;
  title: string;
  content_type: string;
  domain: string;
  description: string;
  growth_potential_score: number;
  difficulty: string;
  duration_minutes: number;
  mood: string;
  source: string;
  url: string;
  thumbnail_url: string;
  video_id: string;
  published_at: string;
  viewed: boolean;
  preview_available: boolean;
}

export interface IdentityNode {
  id: string;
  node_type: string;
  label: string;
  weight: number;
  source: string;
  polarity: string;
}

export interface IdentityGraph {
  user_id: string;
  nodes: IdentityNode[];
  edges: Record<string, unknown>[];
}

export interface AgentStep {
  agent_name: string;
  status: string;
  duration_ms: number;
  detail: Record<string, unknown>;
  created_at: string | null;
}

export interface AgentRun {
  id: string;
  user_id: string;
  trigger_type: string;
  status: string;
  confidence_score: number;
  started_at: string;
  finished_at: string | null;
  steps: AgentStep[];
}

export interface AgentStatus {
  status: string;
  run_id: string | null;
  confidence_score: number | null;
  last_run_at: string | null;
}

export interface UserProfile {
  id: string;
  name: string;
  profile_name: string;
  email: string;
  photo_url: string;
  created_at: string;
}

// ─── API Functions ────────────────────────────────────────────────────────────

export const api = {
  /** Create user, seed identity graph + goals */
  onboardUser: (payload: OnboardingPayload) =>
    req<OnboardingResponse>("/api/v1/onboarding", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  /** Trigger a fresh agent run (async). Returns run_id. */
  triggerAgentRun: (userId: string, triggerType = "user_request") =>
    req<{ run_id: string; status: string; message: string }>("/api/v1/agent/run", {
      method: "POST",
      body: JSON.stringify({ user_id: userId, trigger_type: triggerType }),
    }),

  /** Get current recommendation feed */
  getRecommendations: (userId: string) =>
    req<Recommendation[]>(`/api/v1/recommendations/${userId}`),

  /** Trigger fresh recommendations */
  refreshRecommendations: (userId: string) =>
    req<{ run_id: string; status: string }>("/api/v1/recommendations/refresh", {
      method: "POST",
      body: JSON.stringify({ user_id: userId }),
    }),

  /** Submit feedback signal */
  submitFeedback: (userId: string, contentId: string, interactionType: string) =>
    req<void>(`/api/v1/recommendations/${contentId}/feedback`, {
      method: "POST",
      body: JSON.stringify({ user_id: userId, content_id: contentId, interaction_type: interactionType }),
    }),

  /** All-time feedback count, so giving feedback visibly shapes the curator */
  getFeedbackCount: (userId: string) =>
    req<{ count: number }>(`/api/v1/recommendations/${userId}/feedback-count`),

  /** Agent status */
  getAgentStatus: (userId: string) =>
    req<AgentStatus>(`/api/v1/agent/status/${userId}`),

  /** Agent run history */
  getAgentRuns: (userId: string) =>
    req<AgentRun[]>(`/api/v1/agent/runs/${userId}`),

  /** Full trace for a single run */
  getAgentRunTrace: (runId: string) =>
    req<AgentRun>(`/api/v1/agent/runs/${runId}/trace`),

  /** SSE endpoint streaming step-by-step updates while a run is in progress */
  agentStreamUrl: (runId: string) => `${BASE}/api/v1/agent/stream/${runId}`,

  /** User profile */
  getProfile: (userId: string) =>
    req<UserProfile>(`/api/v1/me/${userId}`),

  /** Goals */
  getGoalSuggestions: () =>
    req<GoalSuggestion[]>("/api/v1/goals/suggestions"),

  getGoals: (userId: string) =>
    req<Goal[]>(`/api/v1/goals/${userId}`),

  createGoal: (userId: string, domain: string, title: string, timeline = "Ongoing") =>
    req<Goal>(`/api/v1/goals/${userId}`, {
      method: "POST",
      body: JSON.stringify({ domain, title, timeline }),
    }),

  updateGoal: (goalId: string, patch: { progress?: number; status?: string; title?: string }) =>
    req<Goal>(`/api/v1/goals/${goalId}`, {
      method: "PATCH",
      body: JSON.stringify(patch),
    }),

  /** Identity graph */
  getIdentityGraph: (userId: string) =>
    req<IdentityGraph>(`/api/v1/identity/${userId}/graph`),

  getIdentitySummary: (userId: string) =>
    req<{ user_id: string; summary: string; node_count: number }>(
      `/api/v1/identity/${userId}/summary`
    ),

  /** Content library */
  getContent: (params?: { domain?: string; content_type?: string; difficulty?: string; user_id?: string; limit?: number }) => {
    const qs = new URLSearchParams();
    if (params?.domain) qs.set("domain", params.domain);
    if (params?.content_type) qs.set("content_type", params.content_type);
    if (params?.difficulty) qs.set("difficulty", params.difficulty);
    if (params?.user_id) qs.set("user_id", params.user_id);
    if (params?.limit) qs.set("limit", String(params.limit));
    return req<ContentItem[]>(`/api/v1/content?${qs}`);
  },

  getMoreLikeThis: (contentType: string, domain?: string) =>
    req<ContentItem[]>("/api/v1/content/more-like-this", {
      method: "POST",
      body: JSON.stringify({ content_type: contentType, domain }),
    }),

  getContentItem: (contentId: string) =>
    req<ContentItem>(`/api/v1/content/${contentId}`),

  recordView: (userId: string, contentId: string) =>
    req<void>(`/api/v1/content/${contentId}/view`, {
      method: "POST",
      body: JSON.stringify({ user_id: userId, content_id: contentId, interaction_type: "viewed" }),
    }),
};
