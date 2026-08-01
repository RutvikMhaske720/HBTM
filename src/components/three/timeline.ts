import * as THREE from "three";
import { POSES, lerpPose, type PoseParams } from "./humanoidPose";

export const DURATION = 23;

function smooth(edge0: number, edge1: number, t: number) {
  return THREE.MathUtils.smoothstep(t, edge0, edge1);
}

export type SceneState = {
  girlPose: PoseParams;
  girlOpacity: number;
  futurePose: PoseParams;
  futureOpacity: number;
  futureScatter: number; // 0 = assembled figure, 1 = scattered dust
  futureRootX: number;
  futureRootZ: number;
  mergeIntoGirl: number; // 0..1, particles collapse toward girl's chest
  chestGlow: number;
  cameraZ: number;
  cameraY: number;
  cameraOrbit: number;
  ambientOpacity: number;
  fogBrightness: number;
};

export function computeSceneState(tRaw: number): SceneState {
  const t = ((tRaw % DURATION) + DURATION) % DURATION;

  // Scene 1 (0-3): sitting, crying, camera dollies in.
  // Scene 2 (3-5): future-self assembles from scattered particles.
  // Scene 3 (5-7): future-self approaches, reaches out.
  // Scene 4 (7-10): girl rises, both open arms.
  // Scene 5 (10-13): embrace.
  // Scene 6 (13-16): future-self dissolves into girl's chest.
  // Scene 7 (16-20): girl stands renewed.
  // Final (20-23): camera orbits, particles fade, loop.

  const girlSitToStand = smooth(7, 10.5, t);
  const girlHugBlend = smooth(9.5, 11, t) - smooth(16, 17.5, t);
  const girlPose = (() => {
    const base = lerpPose(POSES.sitting, POSES.standing, girlSitToStand);
    if (girlHugBlend > 0) return lerpPose(base, POSES.hugging, Math.min(1, girlHugBlend));
    return base;
  })();
  const girlOpacity = smooth(-0.5, 0.6, t);

  const futureAppear = smooth(3, 4.6, t);
  const futureOpacity = futureAppear * (1 - smooth(13.5, 16, t));
  const futureScatter = 1 - smooth(3, 5, t);

  const approach = smooth(5, 7, t);
  const futureRootZ = THREE.MathUtils.lerp(1.6, 0.55, approach);
  const futureRootX = THREE.MathUtils.lerp(0.9, 0.15, approach);

  const reachBlend = smooth(5, 7, t);
  const openBlend = smooth(7, 9, t);
  const hugBlend = smooth(9.5, 11, t);
  const futurePose = (() => {
    let p = lerpPose(POSES.standing, POSES.reachOneArm, reachBlend);
    p = lerpPose(p, POSES.armsOpen, openBlend);
    p = lerpPose(p, POSES.hugging, hugBlend);
    return p;
  })();

  const mergeIntoGirl = smooth(13, 15.5, t);
  const chestGlow = smooth(13, 15, t) * (1 - smooth(21.5, 23, t) * 0.5);

  const cameraZ = THREE.MathUtils.lerp(6.4, 3.6, smooth(0, 3, t));
  const cameraY = THREE.MathUtils.lerp(1.35, 1.15, smooth(0, 3, t));
  const cameraOrbit = smooth(20, 23, t) * Math.PI * 0.45;

  const ambientOpacity = 1 - smooth(21, 23, t) * 0.7;
  const fogBrightness = smooth(16, 20, t) * 0.5;

  return {
    girlPose,
    girlOpacity,
    futurePose,
    futureOpacity,
    futureScatter,
    futureRootX,
    futureRootZ,
    mergeIntoGirl,
    chestGlow,
    cameraZ,
    cameraY,
    cameraOrbit,
    ambientOpacity,
    fogBrightness,
  };
}
