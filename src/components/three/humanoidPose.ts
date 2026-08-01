import * as THREE from "three";

/**
 * Procedural stand-in for a rigged 3D character. There's no character asset
 * (GLTF/motion-capture) in this project, so the figure is a particle cloud
 * sampled over simple jointed primitives (sphere head, tapered-cylinder
 * torso/limbs). Poses are joint angles, not raw point positions, so blending
 * between two poses (lerp the angles, then resample) bends limbs naturally
 * instead of particles drifting straight through the body.
 */

export type PoseParams = {
  hipY: number;
  spineBend: number;
  headDroop: number;
  armPitchL: number;
  armSpreadL: number;
  armPitchR: number;
  armSpreadR: number;
  hipBend: number;
  kneeBend: number;
};

export const POSES = {
  sitting: {
    hipY: 0.5,
    spineBend: 0.45,
    headDroop: 0.7,
    armPitchL: 1.15,
    armSpreadL: 0.35,
    armPitchR: 1.15,
    armSpreadR: 0.35,
    hipBend: 1.45,
    kneeBend: 1.45,
  },
  standing: {
    hipY: 0.9,
    spineBend: 0,
    headDroop: 0,
    armPitchL: 0,
    armSpreadL: 0.15,
    armPitchR: 0,
    armSpreadR: 0.15,
    hipBend: 0,
    kneeBend: 0,
  },
  reachOneArm: {
    hipY: 0.9,
    spineBend: 0.08,
    headDroop: 0,
    armPitchL: 0,
    armSpreadL: 0.15,
    armPitchR: 1.15,
    armSpreadR: 0.55,
    hipBend: 0,
    kneeBend: 0,
  },
  armsOpen: {
    hipY: 0.9,
    spineBend: 0.05,
    headDroop: -0.05,
    armPitchL: 1.0,
    armSpreadL: 0.95,
    armPitchR: 1.0,
    armSpreadR: 0.95,
    hipBend: 0,
    kneeBend: 0,
  },
  hugging: {
    hipY: 0.9,
    spineBend: 0.05,
    headDroop: 0.1,
    armPitchL: 1.35,
    armSpreadL: -0.2,
    armPitchR: 1.35,
    armSpreadR: -0.2,
    hipBend: 0,
    kneeBend: 0,
  },
} as const satisfies Record<string, PoseParams>;

export type PoseName = keyof typeof POSES;

export function lerpPose(a: PoseParams, b: PoseParams, t: number): PoseParams {
  const l = THREE.MathUtils.lerp;
  return {
    hipY: l(a.hipY, b.hipY, t),
    spineBend: l(a.spineBend, b.spineBend, t),
    headDroop: l(a.headDroop, b.headDroop, t),
    armPitchL: l(a.armPitchL, b.armPitchL, t),
    armSpreadL: l(a.armSpreadL, b.armSpreadL, t),
    armPitchR: l(a.armPitchR, b.armPitchR, t),
    armSpreadR: l(a.armSpreadR, b.armSpreadR, t),
    hipBend: l(a.hipBend, b.hipBend, t),
    kneeBend: l(a.kneeBend, b.kneeBend, t),
  };
}

const HEAD_R = 0.14;
const TORSO_LEN = 0.5;
const TORSO_R_HIP = 0.24;
const TORSO_R_SHOULDER = 0.19;
const HIP_R = 0.22;
const SHOULDER_OFFSET = 0.26;
const HIP_OFFSET = 0.11;
const ARM_LEN = 0.52;
const ARM_R = 0.055;
const THIGH_LEN = 0.44;
const SHIN_LEN = 0.44;
const LEG_R_TOP = 0.09;
const LEG_R_BOTTOM = 0.06;

type Part =
  | "head"
  | "torso"
  | "hips"
  | "armL"
  | "armR"
  | "thighL"
  | "thighR"
  | "shinL"
  | "shinR";

const PART_WEIGHTS: [Part, number][] = [
  ["head", 0.08],
  ["torso", 0.26],
  ["hips", 0.08],
  ["armL", 0.1],
  ["armR", 0.1],
  ["thighL", 0.13],
  ["thighR", 0.13],
  ["shinL", 0.06],
  ["shinR", 0.06],
];

export type ParticleSeed = {
  part: Part;
  u: number;
  angle: number;
  jitter: number;
};

export function makeParticleSeeds(count: number): ParticleSeed[] {
  const seeds: ParticleSeed[] = [];
  const totalWeight = PART_WEIGHTS.reduce((sum, [, w]) => sum + w, 0);
  let partIdx = 0;
  let consumed = 0;
  let boundary = PART_WEIGHTS[0][1] * count;

  for (let i = 0; i < count; i++) {
    while (i >= boundary && partIdx < PART_WEIGHTS.length - 1) {
      partIdx++;
      consumed = boundary;
      boundary = consumed + PART_WEIGHTS[partIdx][1] * count;
    }
    seeds.push({
      part: PART_WEIGHTS[partIdx][0],
      u: Math.random(),
      angle: Math.random() * Math.PI * 2,
      jitter: Math.random(),
    });
  }
  void totalWeight;
  return seeds;
}

function limbPoint(
  start: THREE.Vector3,
  dir: THREE.Vector3,
  length: number,
  rNear: number,
  rFar: number,
  seed: ParticleSeed,
  out: THREE.Vector3,
) {
  const r = THREE.MathUtils.lerp(rNear, rFar, seed.u) * (0.35 + 0.65 * seed.jitter);
  const ref = Math.abs(dir.y) < 0.9 ? UP : RIGHT;
  const perp1 = _p1.crossVectors(dir, ref).normalize();
  const perp2 = _p2.crossVectors(dir, perp1).normalize();
  out
    .copy(start)
    .addScaledVector(dir, seed.u * length)
    .addScaledVector(perp1, Math.cos(seed.angle) * r)
    .addScaledVector(perp2, Math.sin(seed.angle) * r);
}

function armDir(pitch: number, spread: number, side: -1 | 1, out: THREE.Vector3) {
  out.set(
    side * Math.sin(spread),
    -Math.cos(pitch),
    Math.sin(pitch) * Math.cos(spread),
  ).normalize();
}

const UP = new THREE.Vector3(0, 1, 0);
const RIGHT = new THREE.Vector3(1, 0, 0);
const _p1 = new THREE.Vector3();
const _p2 = new THREE.Vector3();
const _spineDir = new THREE.Vector3();
const _headDir = new THREE.Vector3();
const _hipCenter = new THREE.Vector3();
const _shoulderCenter = new THREE.Vector3();
const _shoulderL = new THREE.Vector3();
const _shoulderR = new THREE.Vector3();
const _hipL = new THREE.Vector3();
const _hipR = new THREE.Vector3();
const _armDirL = new THREE.Vector3();
const _armDirR = new THREE.Vector3();
const _thighDirL = new THREE.Vector3();
const _thighDirR = new THREE.Vector3();
const _shinDirL = new THREE.Vector3();
const _shinDirR = new THREE.Vector3();
const _kneeL = new THREE.Vector3();
const _kneeR = new THREE.Vector3();
const _headCenter = new THREE.Vector3();

/** Writes world-ish (root-relative) positions for every seed into `positions` (xyz-interleaved). */
export function sampleHumanoid(
  seeds: ParticleSeed[],
  pose: PoseParams,
  positions: Float32Array,
) {
  _spineDir.set(0, Math.cos(pose.spineBend), Math.sin(pose.spineBend)).normalize();
  _headDir
    .set(0, Math.cos(pose.spineBend + pose.headDroop), Math.sin(pose.spineBend + pose.headDroop))
    .normalize();

  _hipCenter.set(0, pose.hipY, 0);
  _shoulderCenter.copy(_hipCenter).addScaledVector(_spineDir, TORSO_LEN);
  _headCenter.copy(_shoulderCenter).addScaledVector(_headDir, 0.1 + HEAD_R * 1.1);

  _shoulderL.copy(_shoulderCenter).addScaledVector(RIGHT, -SHOULDER_OFFSET);
  _shoulderR.copy(_shoulderCenter).addScaledVector(RIGHT, SHOULDER_OFFSET);
  _hipL.copy(_hipCenter).addScaledVector(RIGHT, -HIP_OFFSET);
  _hipR.copy(_hipCenter).addScaledVector(RIGHT, HIP_OFFSET);

  armDir(pose.armPitchL, pose.armSpreadL, -1, _armDirL);
  armDir(pose.armPitchR, pose.armSpreadR, 1, _armDirR);

  _thighDirL.set(0, -Math.cos(pose.hipBend), Math.sin(pose.hipBend)).normalize();
  _thighDirR.copy(_thighDirL);
  const shinAngle = pose.hipBend - pose.kneeBend;
  _shinDirL.set(0, -Math.cos(shinAngle), Math.sin(shinAngle)).normalize();
  _shinDirR.copy(_shinDirL);

  _kneeL.copy(_hipL).addScaledVector(_thighDirL, THIGH_LEN);
  _kneeR.copy(_hipR).addScaledVector(_thighDirR, THIGH_LEN);

  const tmp = _tmpPoint;
  for (let i = 0; i < seeds.length; i++) {
    const seed = seeds[i];
    switch (seed.part) {
      case "head": {
        const phi = seed.u * Math.PI;
        const r = HEAD_R * (0.75 + 0.25 * seed.jitter);
        tmp.set(
          Math.sin(phi) * Math.cos(seed.angle) * r,
          Math.cos(phi) * r,
          Math.sin(phi) * Math.sin(seed.angle) * r,
        );
        // Rotate the local sphere offset by the same forward tilt as the head direction.
        rotateAroundX(tmp, pose.spineBend + pose.headDroop);
        tmp.add(_headCenter);
        break;
      }
      case "torso":
        limbPoint(_hipCenter, _spineDir, TORSO_LEN, TORSO_R_HIP, TORSO_R_SHOULDER, seed, tmp);
        break;
      case "hips": {
        const phi = seed.u * Math.PI;
        const r = HIP_R * (0.7 + 0.3 * seed.jitter);
        tmp.set(
          Math.sin(phi) * Math.cos(seed.angle) * r,
          Math.cos(phi) * r * 0.6 - 0.05,
          Math.sin(phi) * Math.sin(seed.angle) * r,
        );
        tmp.add(_hipCenter);
        break;
      }
      case "armL":
        limbPoint(_shoulderL, _armDirL, ARM_LEN, ARM_R, ARM_R * 0.75, seed, tmp);
        break;
      case "armR":
        limbPoint(_shoulderR, _armDirR, ARM_LEN, ARM_R, ARM_R * 0.75, seed, tmp);
        break;
      case "thighL":
        limbPoint(_hipL, _thighDirL, THIGH_LEN, LEG_R_TOP, LEG_R_TOP * 0.85, seed, tmp);
        break;
      case "thighR":
        limbPoint(_hipR, _thighDirR, THIGH_LEN, LEG_R_TOP, LEG_R_TOP * 0.85, seed, tmp);
        break;
      case "shinL":
        limbPoint(_kneeL, _shinDirL, SHIN_LEN, LEG_R_TOP * 0.8, LEG_R_BOTTOM, seed, tmp);
        break;
      case "shinR":
        limbPoint(_kneeR, _shinDirR, SHIN_LEN, LEG_R_TOP * 0.8, LEG_R_BOTTOM, seed, tmp);
        break;
    }
    positions[i * 3] = tmp.x;
    positions[i * 3 + 1] = tmp.y;
    positions[i * 3 + 2] = tmp.z;
  }
}

const _tmpPoint = new THREE.Vector3();

function rotateAroundX(v: THREE.Vector3, angle: number) {
  const y = v.y;
  const z = v.z;
  const c = Math.cos(angle);
  const s = Math.sin(angle);
  v.y = y * c - z * s;
  v.z = y * s + z * c;
}

/** Approximate chest-height point in root-relative space, for the dissolve/glow target. */
export function chestPoint(pose: PoseParams, out: THREE.Vector3) {
  _spineDir.set(0, Math.cos(pose.spineBend), Math.sin(pose.spineBend)).normalize();
  out.set(0, pose.hipY, 0).addScaledVector(_spineDir, TORSO_LEN * 0.65);
}
