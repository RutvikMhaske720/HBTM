"use client";
import { create } from "zustand";
import { persist } from "zustand/middleware";

interface Profile {
  userId: string;
  name: string;
}

interface IdentityState {
  userId: string | null;
  profile: Profile | null;
  onboardingComplete: boolean;
  setUserId: (id: string) => void;
  setProfile: (profile: Profile) => void;
  setOnboardingComplete: (v: boolean) => void;
  clear: () => void;
}

export const useIdentityStore = create<IdentityState>()(
  persist(
    (set) => ({
      userId: null,
      profile: null,
      onboardingComplete: false,
      setUserId: (id) => set({ userId: id }),
      setProfile: (profile) => set({ profile }),
      setOnboardingComplete: (v) => set({ onboardingComplete: v }),
      clear: () => set({ userId: null, profile: null, onboardingComplete: false }),
    }),
    { name: "iabtm-identity" }
  )
);
