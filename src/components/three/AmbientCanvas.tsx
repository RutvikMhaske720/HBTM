"use client";
/* eslint-disable react-hooks/purity, react-hooks/immutability --
   react-three-fiber renders imperatively: geometry is seeded once via
   useMemo and buffer arrays are mutated in place every frame via useFrame.
   That's the standard, required R3F performance pattern (it avoids 60x/sec
   React re-renders), which the React Compiler's purity assumptions don't
   model. */

import { useMemo, useRef } from "react";
import * as THREE from "three";
import { Canvas, useFrame } from "@react-three/fiber";
import { getSoftDiscTexture } from "./particleTexture";

const COUNT = 140;

function Dust() {
  const discTexture = useMemo(() => getSoftDiscTexture(), []);
  const base = useMemo(() => {
    const arr = new Float32Array(COUNT * 3);
    for (let i = 0; i < COUNT; i++) {
      arr[i * 3] = (Math.random() - 0.5) * 9;
      arr[i * 3 + 1] = (Math.random() - 0.5) * 3;
      arr[i * 3 + 2] = (Math.random() - 0.5) * 4;
    }
    return arr;
  }, []);
  const positions = useMemo(() => new Float32Array(base), [base]);
  const phase = useMemo(
    () => Array.from({ length: COUNT }, () => Math.random() * Math.PI * 2),
    [],
  );
  const geomRef = useRef<THREE.BufferGeometry>(null);

  useFrame(({ clock }) => {
    const t = clock.getElapsedTime();
    for (let i = 0; i < COUNT; i++) {
      const p = phase[i];
      positions[i * 3] = base[i * 3] + Math.sin(t * 0.1 + p) * 0.4;
      positions[i * 3 + 1] = base[i * 3 + 1] + Math.sin(t * 0.08 + p * 1.7) * 0.3;
      positions[i * 3 + 2] = base[i * 3 + 2] + Math.cos(t * 0.09 + p) * 0.3;
    }
    if (geomRef.current) geomRef.current.attributes.position.needsUpdate = true;
  });

  return (
    <points>
      <bufferGeometry ref={geomRef}>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} count={COUNT} />
      </bufferGeometry>
      <pointsMaterial
        map={discTexture}
        color="#f0d9a0"
        size={0.06}
        sizeAttenuation
        transparent
        opacity={0.55}
        depthWrite={false}
        blending={THREE.AdditiveBlending}
      />
    </points>
  );
}

/** Lightweight ambient dust field — no figures, no postprocessing. For accent banners, not the hero. */
export default function AmbientCanvas() {
  return (
    <Canvas
      dpr={[1, 1.5]}
      gl={{ antialias: true }}
      camera={{ fov: 50, position: [0, 0, 4.5] }}
    >
      <Dust />
    </Canvas>
  );
}
