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
const TYPES = ["Videos", "Music", "Art", "Animation", "Editorial", "Print", "Podcast"];
const FILTERS = ["Active paths", "All curated", "Global"] as const;
type Filter = typeof FILTERS[number];
const NEW_WINDOW_MS = 14 * 24 * 60 * 60 * 1000;

function isNew(item: ContentItem) {
  return !item.viewed && Date.now() - new Date(item.published_at).getTime() <= NEW_WINDOW_MS;
}

/** Turn the curator's rejection counts into one plain sentence. */
function describeRejections(rejected: Record<string, number>) {
  const reasons: Record<string, string> = {
    irrelevant: "not close enough to your profile",
    stale: "older than the freshness window",
    duplicate: "already in your library",
    already_known: "already curated for you",
    no_preview: "had no preview image",
    bad_link: "had no usable link",
    dead_link: "had a dead link",
    undated: "had no publication date",
    unusable_title: "looked like engagement bait",
  };
  const parts = Object.entries(rejected)
    .filter(([key, count]) => count > 0 && key in reasons)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3)
    .map(([key, count]) => `${count} ${reasons[key]}`);
  return parts.length ? parts.join(", ") : "";
}

export default function LibraryPage() {
  const userId = useIdentityStore((state) => state.userId);
  const [items, setItems] = useState<ContentItem[]>([]);
  const [goals, setGoals] = useState<Goal[]>([]);
  const [contentType, setContentType] = useState("Videos");
  const [filter, setFilter] = useState<Filter>("Active paths");
  const [query, setQuery] = useState("");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [gettingMore, setGettingMore] = useState(false);
  const [activeItem, setActiveItem] = useState<ContentItem | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const load = useCallback(async () => {
    try {
      const [content, activeGoals] = await Promise.all([
        // With a search term the backend ranks by meaning through the vector
        // index, so the content-type filter is applied inside that query.
        api.getContent({
          content_type: contentType,
          user_id: userId ?? undefined,
          q: search || undefined,
          limit: 100,
        }),
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
  }, [contentType, search, userId]);

  useEffect(() => {
    const timer = window.setTimeout(() => { void load(); }, 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  // Debounce typing so each keystroke doesn't trigger a semantic query.
  useEffect(() => {
    const timer = window.setTimeout(() => setSearch(query.trim()), 350);
    return () => window.clearTimeout(timer);
  }, [query]);

  const visibleItems = useMemo(() => {
    const activeDomains = new Set(goals.map((goal) => goal.domain));
    return items.filter((item) => {
      if (filter === "Active paths" && !activeDomains.has(item.domain)) return false;
      if (filter === "All curated" && item.source === "web") return false;
      return true;
    });
  }, [filter, goals, items]);

  async function handleGetMore() {
    setGettingMore(true);
    setError("");
    setNotice("");
    try {
      const { items: found, report } = await api.getMoreLikeThis(
        contentType, goals[0]?.domain, userId ?? undefined,
      );
      await load();
      setFilter("Global");
      if (found.length === 0) {
        const why = describeRejections(report.rejected);
        setNotice(
          report.fetched === 0
            ? `No ${contentType.toLowerCase()} sources responded just now. Try again in a moment.`
            : `Checked ${report.fetched} ${contentType.toLowerCase()} results and kept none${why ? ` — ${why}` : ""}.`,
        );
      } else {
        setNotice(`Added ${found.length} new ${contentType.toLowerCase()} ${found.length === 1 ? "item" : "items"}.`);
      }
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
      {notice && <div role="status" className="rounded-xl border border-(--color-border) bg-(--color-bg-offwhite) px-4 py-3 text-sm text-(--color-text-secondary)">{notice}</div>}

      <div className="space-y-4 border-y border-(--color-border) py-4">
        <div className="flex flex-wrap gap-2">
          {TYPES.map((type) => <button key={type} onClick={() => { setLoading(true); setContentType(type); }} className={`rounded-full px-3 py-1.5 text-[13px] font-medium transition-colors ${contentType === type ? "bg-(--color-accent-secondary) text-(--color-text-inverse)" : "border border-(--color-border) text-(--color-ink) hover:bg-(--color-bg-offwhite)"}`}>{type}</button>)}
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {FILTERS.map((item) => <button key={item} onClick={() => setFilter(item)} className={`rounded-full px-3 py-1.5 text-[13px] font-medium transition-colors ${filter === item ? "bg-(--color-bg-offwhite) text-(--color-ink) ring-1 ring-(--color-border)" : "text-(--color-text-secondary) hover:text-(--color-ink)"}`}>{item}</button>)}
          <label className="ml-auto flex min-w-52 items-center rounded-full border border-(--color-border) bg-(--color-surface) px-3 py-1.5">
            <span className="mr-2 text-(--color-text-tertiary)">⌕</span>
            <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search by meaning" className="w-full bg-transparent text-[13px] text-(--color-ink) outline-none placeholder:text-(--color-text-tertiary)" />
          </label>
        </div>
      </div>

      {loading ? <div className="space-y-3">{Array.from({ length: 5 }).map((_, index) => <div key={index} className="h-32 animate-pulse rounded-2xl bg-(--color-border)" />)}</div>
      : visibleItems.length === 0 ? <div className="py-24 text-center text-(--color-text-secondary)">
          {search ? `Nothing in your library matches “${search}”.`
            : `No ${contentType.toLowerCase()} curated for your profile yet — try “Get more like this”.`}
        </div>
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
