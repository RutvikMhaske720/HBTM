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
import { MeshReflectorMaterial } from "@react-three/drei";
import { EffectComposer, Bloom, Vignette } from "@react-three/postprocessing";
import {
  makeParticleSeeds,
  sampleHumanoid,
  chestPoint,
  type ParticleSeed,
} from "./humanoidPose";
import { computeSceneState, DURATION } from "./timeline";
import { getSoftDiscTexture } from "./particleTexture";

const GIRL_COUNT = 3200;
const FUTURE_COUNT = 2400;
const DUST_COUNT = 260;

function randomInSphere(radius: number, out: THREE.Vector3) {
  const u = Math.random();
  const v = Math.random();
  const theta = 2 * Math.PI * u;
  const phi = Math.acos(2 * v - 1);
  const r = radius * (0.5 + 0.5 * Math.random());
  out.set(
    r * Math.sin(phi) * Math.cos(theta),
    1.1 + r * Math.cos(phi) * 0.6,
    r * Math.sin(phi) * Math.sin(theta),
  );
  return out;
}

function Figures({ reduced }: { reduced: boolean }) {
  const girlSeeds = useMemo<ParticleSeed[]>(() => makeParticleSeeds(GIRL_COUNT), []);
  const futureSeeds = useMemo<ParticleSeed[]>(() => makeParticleSeeds(FUTURE_COUNT), []);

  const girlPositions = useMemo(() => new Float32Array(GIRL_COUNT * 3), []);
  const futurePositions = useMemo(() => new Float32Array(FUTURE_COUNT * 3), []);
  const futureAssembled = useMemo(() => new Float32Array(FUTURE_COUNT * 3), []);

  const scatterOffsets = useMemo(() => {
    const arr = new Float32Array(FUTURE_COUNT * 3);
    const v = new THREE.Vector3();
    for (let i = 0; i < FUTURE_COUNT; i++) {
      randomInSphere(2.6, v);
      arr[i * 3] = v.x;
      arr[i * 3 + 1] = v.y;
      arr[i * 3 + 2] = v.z;
    }
    return arr;
  }, []);

  const dustBase = useMemo(() => {
    const arr = new Float32Array(DUST_COUNT * 3);
    for (let i = 0; i < DUST_COUNT; i++) {
      arr[i * 3] = (Math.random() - 0.5) * 8;
      arr[i * 3 + 1] = Math.random() * 3.2;
      arr[i * 3 + 2] = (Math.random() - 0.5) * 6 - 0.5;
    }
    return arr;
  }, []);
  const dustPositions = useMemo(() => new Float32Array(dustBase), [dustBase]);
  const dustPhase = useMemo(
    () => Array.from({ length: DUST_COUNT }, () => Math.random() * Math.PI * 2),
    [],
  );

  const girlGeomRef = useRef<THREE.BufferGeometry>(null);
  const futureGeomRef = useRef<THREE.BufferGeometry>(null);
  const dustGeomRef = useRef<THREE.BufferGeometry>(null);
  const girlMatRef = useRef<THREE.PointsMaterial>(null);
  const futureMatRef = useRef<THREE.PointsMaterial>(null);
  const dustMatRef = useRef<THREE.PointsMaterial>(null);
  const futureGroupRef = useRef<THREE.Group>(null);
  const chestLightRef = useRef<THREE.PointLight>(null);
  const fogRef = useRef<THREE.Fog>(null);

  const chestWorld = useMemo(() => new THREE.Vector3(), []);
  const chestLocal = useMemo(() => new THREE.Vector3(), []);
  const discTexture = useMemo(() => getSoftDiscTexture(), []);

  useFrame(({ camera, clock }) => {
    const t = reduced ? 18 : clock.getElapsedTime() % DURATION;
    const s = computeSceneState(t);

    sampleHumanoid(girlSeeds, s.girlPose, girlPositions);
    if (girlGeomRef.current) {
      girlGeomRef.current.attributes.position.needsUpdate = true;
    }
    if (girlMatRef.current) girlMatRef.current.opacity = s.girlOpacity * 0.9;

    sampleHumanoid(futureSeeds, s.futurePose, futureAssembled);

    chestPoint(s.girlPose, chestWorld);
    chestLocal.set(
      chestWorld.x - s.futureRootX,
      chestWorld.y,
      chestWorld.z - s.futureRootZ,
    );

    for (let i = 0; i < FUTURE_COUNT; i++) {
      const ax = futureAssembled[i * 3];
      const ay = futureAssembled[i * 3 + 1];
      const az = futureAssembled[i * 3 + 2];
      const sx = scatterOffsets[i * 3];
      const sy = scatterOffsets[i * 3 + 1];
      const sz = scatterOffsets[i * 3 + 2];
      const px = THREE.MathUtils.lerp(ax, sx, s.futureScatter);
      const py = THREE.MathUtils.lerp(ay, sy, s.futureScatter);
      const pz = THREE.MathUtils.lerp(az, sz, s.futureScatter);
      futurePositions[i * 3] = THREE.MathUtils.lerp(px, chestLocal.x, s.mergeIntoGirl);
      futurePositions[i * 3 + 1] = THREE.MathUtils.lerp(py, chestLocal.y, s.mergeIntoGirl);
      futurePositions[i * 3 + 2] = THREE.MathUtils.lerp(pz, chestLocal.z, s.mergeIntoGirl);
    }
    if (futureGeomRef.current) {
      futureGeomRef.current.attributes.position.needsUpdate = true;
    }
    if (futureMatRef.current) {
      futureMatRef.current.opacity = s.futureOpacity;
      futureMatRef.current.size = 0.058 * (1 - 0.6 * s.mergeIntoGirl);
    }
    if (futureGroupRef.current) {
      futureGroupRef.current.position.set(s.futureRootX, 0, s.futureRootZ);
    }

    if (chestLightRef.current) {
      chestLightRef.current.position.copy(chestWorld);
      chestLightRef.current.intensity = s.chestGlow * 4.5;
    }

    const time = clock.getElapsedTime();
    for (let i = 0; i < DUST_COUNT; i++) {
      const phase = dustPhase[i];
      dustPositions[i * 3] = dustBase[i * 3] + Math.sin(time * 0.15 + phase) * 0.3;
      dustPositions[i * 3 + 1] = (dustBase[i * 3 + 1] + time * 0.05) % 3.2;
      dustPositions[i * 3 + 2] = dustBase[i * 3 + 2] + Math.cos(time * 0.12 + phase) * 0.3;
    }
    if (dustGeomRef.current) dustGeomRef.current.attributes.position.needsUpdate = true;
    if (dustMatRef.current) dustMatRef.current.opacity = s.ambientOpacity * 0.5;

    if (!reduced) {
      const radius = s.cameraZ;
      camera.position.x = Math.sin(s.cameraOrbit) * radius * 0.55;
      camera.position.z = Math.cos(s.cameraOrbit) * radius;
      camera.position.y = s.cameraY;
      camera.lookAt(0, 1.05, 0.25);
    }

    if (fogRef.current) {
      const b = 0.03 + s.fogBrightness * 0.05;
      fogRef.current.color.setRGB(b, b, b * 1.05);
    }
  });

  return (
    <>
      <fog ref={fogRef} attach="fog" args={[0x030303, 3, 11]} />

      <points>
        <bufferGeometry ref={girlGeomRef}>
          <bufferAttribute
            attach="attributes-position"
            args={[girlPositions, 3]}
            count={GIRL_COUNT}
          />
        </bufferGeometry>
        <pointsMaterial
          ref={girlMatRef}
          map={discTexture}
          color="#0d0d0f"
          size={0.052}
          sizeAttenuation
          transparent
          opacity={0}
          depthWrite={false}
        />
      </points>

      <group ref={futureGroupRef}>
        <points>
          <bufferGeometry ref={futureGeomRef}>
            <bufferAttribute
              attach="attributes-position"
              args={[futurePositions, 3]}
              count={FUTURE_COUNT}
            />
          </bufferGeometry>
          <pointsMaterial
            ref={futureMatRef}
            map={discTexture}
            color="#f4f6ff"
            size={0.058}
            sizeAttenuation
            transparent
            opacity={0}
            depthWrite={false}
            blending={THREE.AdditiveBlending}
          />
        </points>
      </group>

      <points>
        <bufferGeometry ref={dustGeomRef}>
          <bufferAttribute
            attach="attributes-position"
            args={[dustPositions, 3]}
            count={DUST_COUNT}
          />
        </bufferGeometry>
        <pointsMaterial
          ref={dustMatRef}
          map={discTexture}
          color="#cfd6ff"
          size={0.026}
          sizeAttenuation
          transparent
          opacity={0.3}
          depthWrite={false}
          blending={THREE.AdditiveBlending}
        />
      </points>

      <pointLight ref={chestLightRef} color="#dfe6ff" intensity={0} distance={4} decay={2} />

      <mesh position={[0, 0, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <planeGeometry args={[24, 24]} />
        <MeshReflectorMaterial
          blur={[280, 120]}
          resolution={1024}
          mixBlur={8}
          mixStrength={2.2}
          roughness={0.85}
          depthScale={1}
          minDepthThreshold={0.3}
          maxDepthThreshold={1.2}
          color="#040405"
          metalness={0.55}
          mirror={0}
        />
      </mesh>
    </>
  );
}

export default function TransformationCanvas() {
  const reduced = useMemo(
    () =>
      typeof window !== "undefined" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches,
    [],
  );

  return (
    <Canvas
      dpr={[1, 1.8]}
      gl={{ antialias: true, powerPreference: "high-performance" }}
      camera={{ fov: 42, near: 0.1, far: 30, position: [0, 1.35, 6.4] }}
    >
      <color attach="background" args={["#030303"]} />
      <ambientLight intensity={0.18} />
      <directionalLight position={[0, 3.2, -4]} intensity={1.1} color="#dfe6ff" />
      <directionalLight position={[-2, 1.5, 3]} intensity={0.12} color="#ffffff" />

      <Figures reduced={reduced} />

      <EffectComposer>
        <Bloom luminanceThreshold={0.15} luminanceSmoothing={0.9} intensity={1.15} mipmapBlur />
        <Vignette eskil={false} offset={0.25} darkness={0.85} />
      </EffectComposer>
    </Canvas>
  );
}
