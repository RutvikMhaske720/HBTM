"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import VideoModal from "@/components/media/VideoModal";
import { api } from "@/lib/api";
import type { ContentItem, Goal } from "@/lib/api";
import { useIdentityStore } from "@/lib/store/identity.store";

const DOMAIN_COLORS: Record<string, string> = {
  Creativity: "#C97A3D", Mindset: "#6E5AA0", Health: "#5E8F5A", Knowledge: "#3E5E8C",
  Career: "#9C7A3A", Relationships: "#A8497A", Finance: "#7A8C4A", Purpose: "#2F6F6B",
};
const TYPES = ["Film", "Music", "Art", "Animation", "Editorial", "Print"];
const FILTERS = ["Active paths", "All curated", "Global"] as const;
type Filter = typeof FILTERS[number];
const NEW_WINDOW_MS = 14 * 24 * 60 * 60 * 1000;

function isNew(item: ContentItem) {
  return !item.viewed && (item.source !== "internal" || Date.now() - new Date(item.published_at).getTime() <= NEW_WINDOW_MS);
}

export default function LibraryPage() {
  const userId = useIdentityStore((state) => state.userId);
  const [items, setItems] = useState<ContentItem[]>([]);
  const [goals, setGoals] = useState<Goal[]>([]);
  const [contentType, setContentType] = useState("Film");
  const [filter, setFilter] = useState<Filter>("Active paths");
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [gettingMore, setGettingMore] = useState(false);
  const [activeItem, setActiveItem] = useState<ContentItem | null>(null);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      const [content, activeGoals] = await Promise.all([
        api.getContent({ content_type: contentType, user_id: userId ?? undefined, limit: 100 }),
        userId ? api.getGoals(userId) : Promise.resolve([]),
      ]);
      setItems(content);
      setGoals(activeGoals);
    } catch (error) {
      console.error(error);
      setError("The library could not be loaded. Confirm that the backend is running, then try again.");
    } finally {
      setLoading(false);
    }
  }, [contentType, userId]);

  useEffect(() => {
    const timer = window.setTimeout(() => { void load(); }, 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  const visibleItems = useMemo(() => {
    const activeDomains = new Set(goals.map((goal) => goal.domain));
    const normalizedQuery = query.trim().toLowerCase();
    return items.filter((item) => {
      if (filter === "Active paths" && !activeDomains.has(item.domain)) return false;
      if (filter === "All curated" && item.source !== "internal") return false;
      return !normalizedQuery || item.title.toLowerCase().includes(normalizedQuery);
    });
  }, [filter, goals, items, query]);

  async function handleGetMore() {
    setGettingMore(true);
    setError("");
    try {
      await api.getMoreLikeThis(contentType, goals[0]?.domain);
      await load();
      setFilter("Global");
    } catch (error) {
      console.error(error);
      setError("We could not find more media right now. Check the configured content source and try again.");
    } finally {
      setGettingMore(false);
    }
  }

  function openItem(item: ContentItem) {
    setActiveItem(item);
    if (userId && !item.viewed) {
      void api.recordView(userId, item.id).catch(console.error);
      setItems((current) => current.map((entry) => entry.id === item.id ? { ...entry, viewed: true } : entry));
    }
  }

  return (
    <div className="max-w-5xl space-y-7">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-[13px] uppercase tracking-widest text-(--color-text-tertiary)">IABTM curated</p>
          <h1 className="mt-1 text-3xl font-bold tracking-tight text-(--color-ink)">Curated Media</h1>
          <p className="mt-1 text-[15px] text-(--color-text-secondary)">A considered library for the path you are building.</p>
        </div>
        <button
          onClick={handleGetMore}
          disabled={gettingMore}
          className="rounded-full bg-(--color-accent-secondary) px-4 py-2 text-[13px] font-medium text-(--color-text-inverse) transition-opacity hover:opacity-90 disabled:opacity-50"
        >
          {gettingMore ? "Finding media…" : "Get more like this"}
        </button>
      </header>

      {error && <div role="alert" className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">{error}</div>}

      <div className="space-y-4 border-y border-(--color-border) py-4">
        <div className="flex flex-wrap gap-2">
          {TYPES.map((type) => <button key={type} onClick={() => { setLoading(true); setContentType(type); }} className={`rounded-full px-3 py-1.5 text-[13px] font-medium transition-colors ${contentType === type ? "bg-(--color-accent-secondary) text-(--color-text-inverse)" : "border border-(--color-border) text-(--color-ink) hover:bg-(--color-bg-offwhite)"}`}>{type}</button>)}
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {FILTERS.map((item) => <button key={item} onClick={() => setFilter(item)} className={`rounded-full px-3 py-1.5 text-[13px] font-medium transition-colors ${filter === item ? "bg-(--color-bg-offwhite) text-(--color-ink) ring-1 ring-(--color-border)" : "text-(--color-text-secondary) hover:text-(--color-ink)"}`}>{item}</button>)}
          <label className="ml-auto flex min-w-52 items-center rounded-full border border-(--color-border) bg-(--color-surface) px-3 py-1.5">
            <span className="mr-2 text-(--color-text-tertiary)">⌕</span>
            <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search media" className="w-full bg-transparent text-[13px] text-(--color-ink) outline-none placeholder:text-(--color-text-tertiary)" />
          </label>
        </div>
      </div>

      {loading ? <div className="space-y-3">{Array.from({ length: 5 }).map((_, index) => <div key={index} className="h-32 animate-pulse rounded-2xl bg-(--color-border)" />)}</div>
      : visibleItems.length === 0 ? <div className="py-24 text-center text-(--color-text-secondary)">No media matches this view yet.</div>
      : <div className="space-y-3">{visibleItems.map((item) => {
        const color = DOMAIN_COLORS[item.domain] ?? "#8a8a8a";
        const fresh = isNew(item);
        return <article key={item.id} className="flex gap-4 rounded-2xl border border-(--color-border) bg-(--color-surface) p-3 transition-shadow hover:shadow-md">
          <div className="h-28 w-40 shrink-0 overflow-hidden rounded-xl" style={{ background: color }}>
            {item.thumbnail_url ? <img src={item.thumbnail_url} alt="" className="h-full w-full object-cover" /> : <div className="flex h-full items-center justify-center text-xs font-semibold text-white/80">{item.domain}</div>}
          </div>
          <div className="flex min-w-0 flex-1 flex-col py-1">
            <div className="flex items-center gap-2 text-[11px] font-medium"><span style={{ color }}>{item.content_type}</span><span className="text-(--color-text-tertiary)">{item.domain}</span></div>
            <h2 className="mt-1 text-[15px] font-semibold text-(--color-ink)">{item.title}</h2>
            <p className="mt-1 line-clamp-2 text-[13px] leading-relaxed text-(--color-text-secondary)">{item.description}</p>
            <div className="mt-auto flex items-center justify-between pt-2"><span className="text-[12px] text-(--color-text-tertiary)">{item.duration_minutes}m · {item.difficulty}</span><button onClick={() => openItem(item)} className={`rounded-full px-3 py-1 text-[12px] font-semibold ${fresh ? "bg-(--color-accent-secondary) text-(--color-text-inverse)" : "border border-(--color-border) text-(--color-ink) hover:bg-(--color-bg-offwhite)"}`}>{fresh ? "New" : item.preview_available ? "Preview" : item.url ? "Open" : "Details"}</button></div>
          </div>
        </article>;
      })}</div>}
      <VideoModal item={activeItem} onClose={() => setActiveItem(null)} />
    </div>
  );
}
