"use client";

import dynamic from "next/dynamic";

const AmbientCanvas = dynamic(() => import("@/components/three/AmbientCanvas"), {
  ssr: false,
});

export default function AmbientBackdrop({ className = "" }: { className?: string }) {
  return (
    <div className={`pointer-events-none absolute inset-0 ${className}`}>
      <AmbientCanvas />
    </div>
  );
}
