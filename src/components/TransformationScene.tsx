"use client";

import dynamic from "next/dynamic";

const TransformationCanvas = dynamic(
  () => import("@/components/three/TransformationCanvas"),
  { ssr: false },
);

/**
 * Cinematic hero: a present-self silhouette (sitting, head down) is joined by
 * a particle "future self" that approaches, embraces her, and dissolves into
 * a chest-glow — looping ~23s. Built as a procedural particle scene (no
 * rigged character asset exists in this project) rather than a live-action
 * video, so it renders instantly and loops seamlessly in the browser.
 */
export default function TransformationScene({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="relative h-screen w-full overflow-hidden bg-(--color-ink)">
      <TransformationCanvas />

      <div className="pointer-events-none absolute inset-0 bg-linear-to-b from-(--color-ink)/40 via-transparent to-(--color-ink)/80" />

      <div className="absolute inset-0 z-10 flex flex-col items-center justify-center px-6 text-center">
        {children}
      </div>
    </div>
  );
}
