"use client";

import { useState, useRef, useEffect } from "react";
import { useIdentityStore } from "@/lib/store/identity.store";
import { api } from "@/lib/api";
import type { Recommendation } from "@/lib/api";

interface Message {
  role: "user" | "assistant";
  content: string;
  recs?: Recommendation[];
}

export default function ChatPage() {
  const userId = useIdentityStore((s) => s.userId);
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "Hi! I'm your AI Curator. Ask me what you should focus on, explore your goals, or request a personalized recommendation.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend() {
    if (!input.trim() || loading) return;
    const userMsg = input.trim();
    setInput("");
    setMessages((m) => [...m, { role: "user", content: userMsg }]);
    setLoading(true);

    try {
      // For MVP: fetch recommendations that are "relevant" to the question
      // and compose a simulated curator response
      const recs = userId ? await api.getRecommendations(userId) : [];
      const topRecs = recs.slice(0, 3);

      const lowerMsg = userMsg.toLowerCase();
      let response = "";

      if (lowerMsg.includes("focus") || lowerMsg.includes("today") || lowerMsg.includes("should")) {
        const domains = [...new Set(topRecs.map((r) => r.domain))].slice(0, 2).join(" and ");
        response = `Based on your identity graph and active goals, I'd suggest focusing on **${domains || "your top goal"}** today. I've pulled the most relevant pieces for you below.`;
      } else if (lowerMsg.includes("goal") || lowerMsg.includes("path")) {
        response = `Your path is shaped by the goals you set during onboarding. The content below is specifically scored against your growth vector — the gap between your current and imagined self.`;
      } else if (lowerMsg.includes("recommend") || lowerMsg.includes("suggest") || lowerMsg.includes("watch") || lowerMsg.includes("read")) {
        response = `Here are the highest-scoring items from your current curation run, ranked by goal alignment and growth potential:`;
      } else {
        response = `That's a great question. Let me surface the most relevant content from your personalized feed to help you think this through.`;
      }

      setMessages((m) => [
        ...m,
        { role: "assistant", content: response, recs: topRecs.length > 0 ? topRecs : undefined },
      ]);
    } catch (err) {
      console.error(err);
      setMessages((m) => [
        ...m,
        { role: "assistant", content: "I'm having trouble connecting to the backend. Please ensure the API server is running." },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col max-w-3xl mx-auto">
      <div className="mb-6">
        <p className="text-[13px] uppercase tracking-widest text-(--color-text-tertiary)">AI Companion</p>
        <h1 className="mt-1 text-3xl font-bold tracking-tight text-(--color-ink)">Chat with Curator</h1>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-4 pb-4">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-[85%] ${msg.role === "user" ? "order-2" : "order-1"}`}>
              {msg.role === "assistant" && (
                <div className="mb-1.5 flex items-center gap-2">
                  <span className="h-5 w-5 rounded-full bg-(--color-accent-secondary) flex items-center justify-center text-[9px] text-white font-bold">
                    AI
                  </span>
                  <span className="text-[11px] text-(--color-text-tertiary)">Curator</span>
                </div>
              )}
              <div
                className={`rounded-2xl px-4 py-3 text-[14px] leading-relaxed ${
                  msg.role === "user"
                    ? "bg-(--color-ink) text-white rounded-tr-sm"
                    : "bg-(--color-bg-offwhite) text-(--color-ink) rounded-tl-sm border border-(--color-border)"
                }`}
              >
                {msg.content}
              </div>

              {/* Embedded recommendation cards */}
              {msg.recs && msg.recs.length > 0 && (
                <div className="mt-3 space-y-2">
                  {msg.recs.map((rec) => (
                    <div
                      key={rec.id}
                      className="flex items-start gap-3 rounded-xl border border-(--color-border) bg-white p-3"
                    >
                      <div
                        className="mt-0.5 h-3 w-3 flex-shrink-0 rounded-full"
                        style={{ background: "#5A4FF3" }}
                      />
                      <div>
                        <p className="text-[13px] font-semibold text-(--color-ink)">{rec.title}</p>
                        <p className="text-[11px] text-(--color-text-tertiary)">
                          {rec.content_type} · {rec.domain} · {rec.duration_minutes}m
                        </p>
                        <p className="mt-1 text-[11px] text-(--color-accent-secondary)">
                          ✦ {rec.why_recommended}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="flex items-center gap-1.5 rounded-2xl bg-(--color-bg-offwhite) border border-(--color-border) px-4 py-3">
              {[0, 150, 300].map((delay) => (
                <span
                  key={delay}
                  className="h-1.5 w-1.5 rounded-full bg-(--color-accent-secondary) animate-bounce"
                  style={{ animationDelay: `${delay}ms` }}
                />
              ))}
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="flex gap-3 border-t border-(--color-border) pt-4">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
          placeholder="Ask your curator anything…"
          className="flex-1 rounded-full border border-(--color-border) bg-white px-5 py-3 text-[14px] outline-none focus:ring-2 focus:ring-(--color-accent-secondary)"
        />
        <button
          onClick={handleSend}
          disabled={!input.trim() || loading}
          className="rounded-full bg-(--color-ink) px-6 py-3 text-[14px] font-medium text-white disabled:opacity-40 transition-opacity"
        >
          Send
        </button>
      </div>
    </div>
  );
}
