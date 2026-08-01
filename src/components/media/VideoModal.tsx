"use client";

import { useEffect } from "react";
import type { ContentItem } from "@/lib/api";

interface VideoModalProps {
  item: ContentItem | null;
  onClose: () => void;
}

export default function VideoModal({ item, onClose }: VideoModalProps) {
  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  if (!item) return null;

  const canPlayYoutube = item.preview_available && item.video_id;
  const spotifyEmbedUrl = item.source === "spotify" && item.url.includes("open.spotify.com/track/")
    ? item.url.replace("open.spotify.com/track/", "open.spotify.com/embed/track/")
    : "";
  const destination = item.url || (item.video_id ? `https://www.youtube.com/watch?v=${item.video_id}` : "");
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
      role="dialog"
      aria-modal="true"
      aria-label={`${item.title} preview`}
      onMouseDown={onClose}
    >
      <div
        className="w-full max-w-3xl overflow-hidden rounded-2xl bg-(--color-surface) shadow-2xl"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-(--color-border) px-5 py-4">
          <div className="min-w-0">
            <p className="text-[11px] font-semibold uppercase tracking-wider text-(--color-text-tertiary)">{item.content_type}</p>
            <h2 className="truncate text-base font-semibold text-(--color-ink)">{item.title}</h2>
          </div>
          <button onClick={onClose} className="ml-4 rounded-full px-3 py-1 text-sm text-(--color-text-secondary) hover:bg-(--color-bg-offwhite) hover:text-(--color-ink)">Close</button>
        </div>
        {canPlayYoutube ? (
          <iframe
            className="aspect-video w-full bg-black"
            src={`https://www.youtube.com/embed/${item.video_id}`}
            title={item.title}
            allow="autoplay; encrypted-media"
            allowFullScreen
          />
        ) : spotifyEmbedUrl ? (
          <iframe
            className="h-[352px] w-full bg-(--color-bg-offwhite)"
            src={spotifyEmbedUrl}
            title={`${item.title} on Spotify`}
            allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"
            loading="lazy"
          />
        ) : item.thumbnail_url ? (
          <div className="flex max-h-[65vh] items-center justify-center bg-(--color-bg-offwhite) p-4">
            <img src={item.thumbnail_url} alt={item.title} className="max-h-[58vh] max-w-full rounded-xl object-contain" />
          </div>
        ) : (
          <div className="flex aspect-video flex-col items-center justify-center bg-(--color-bg-offwhite) px-8 text-center">
            <span className="text-3xl">◻</span>
            <p className="mt-3 text-base font-semibold text-(--color-ink)">No in-app preview</p>
            <p className="mt-1 max-w-md text-sm leading-relaxed text-(--color-text-secondary)">
              {item.description || "This source does not provide an embeddable preview."}
            </p>
          </div>
        )}
        <div className="flex justify-end border-t border-(--color-border) px-5 py-3">
          {destination ? (
            <a
              href={destination}
              target="_blank"
              rel="noreferrer"
              className="rounded-full bg-(--color-accent-secondary) px-4 py-2 text-sm font-medium text-(--color-text-inverse) hover:opacity-90"
            >
              Open source ↗
            </a>
          ) : <p className="text-sm text-(--color-text-secondary)">No source link has been added yet.</p>}
        </div>
      </div>
    </div>
  );
}
