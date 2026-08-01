import * as THREE from "three";

let cached: THREE.CanvasTexture | null = null;

/**
 * THREE.PointsMaterial renders flat squares by default. A soft radial-falloff
 * sprite is what makes particles read as glowing dots/stars instead of
 * pixelated blocks — this is the single biggest lever for matching a
 * "premium VFX" particle look.
 */
export function getSoftDiscTexture(): THREE.CanvasTexture {
  if (cached) return cached;
  const size = 128;
  const canvas = document.createElement("canvas");
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext("2d")!;
  const r = size / 2;
  const gradient = ctx.createRadialGradient(r, r, 0, r, r, r);
  gradient.addColorStop(0, "rgba(255,255,255,1)");
  gradient.addColorStop(0.35, "rgba(255,255,255,0.85)");
  gradient.addColorStop(0.7, "rgba(255,255,255,0.22)");
  gradient.addColorStop(1, "rgba(255,255,255,0)");
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, size, size);

  const tex = new THREE.CanvasTexture(canvas);
  tex.needsUpdate = true;
  cached = tex;
  return tex;
}
