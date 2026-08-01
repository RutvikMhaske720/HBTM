"use client";

import type { ContentItem } from "@/lib/api";

interface VideoModalProps {
  item: ContentItem | null;
  onClose: () => void;
}

export default function VideoModal({ item, onClose }: VideoModalProps) {
  if (!item) return null;

  const canPlay = item.preview_available && item.video_id;
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
        {canPlay ? (
          <iframe
            className="aspect-video w-full bg-black"
            src={`https://www.youtube.com/embed/${item.video_id}`}
            title={item.title}
            allow="autoplay; encrypted-media"
            allowFullScreen
          />
        ) : (
          <div className="flex aspect-video flex-col items-center justify-center bg-(--color-bg-offwhite) px-8 text-center">
            <span className="text-3xl">◻</span>
            <p className="mt-3 text-base font-semibold text-(--color-ink)">Preview unavailable</p>
            <p className="mt-1 max-w-md text-sm leading-relaxed text-(--color-text-secondary)">
              This item does not have a playable video preview yet. Mocked source results become playable when a real source connection is configured.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
