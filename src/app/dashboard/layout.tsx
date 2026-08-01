"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useIdentityStore } from "@/lib/store/identity.store";
import Sidebar from "@/components/layout/Sidebar";
import TopNav from "@/components/layout/TopNav";
import { supabase } from "@/lib/supabase";
import { api } from "@/lib/api";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const userId = useIdentityStore((s) => s.userId);
  const setUserId = useIdentityStore((s) => s.setUserId);
  const setProfile = useIdentityStore((s) => s.setProfile);
  const setOnboardingComplete = useIdentityStore((s) => s.setOnboardingComplete);
  const [checkingSession, setCheckingSession] = useState(true);
  const router = useRouter();

  useEffect(() => {
    let active = true;
    void supabase.auth.getSession().then(async ({ data: { session } }) => {
      if (!active) return;
      if (!session) {
        router.replace("/auth");
        return;
      }
      const authUser = session.user;
      setUserId(authUser.id);
      try {
        const profile = await api.getProfile(authUser.id);
        if (!active) return;
        setProfile({ userId: profile.id, name: profile.name });
        setOnboardingComplete(true);
      } catch {
        router.replace("/onboarding");
        return;
      } finally {
        if (active) setCheckingSession(false);
      }
    });
    return () => { active = false; };
  }, [router, setOnboardingComplete, setProfile, setUserId]);

  if (checkingSession || !userId) return null;

  return (
    <div className="flex h-screen overflow-hidden bg-(--color-bg-primary)">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <TopNav />
        <main className="flex-1 overflow-y-auto px-6 py-8 lg:px-10">
          {children}
        </main>
      </div>
    </div>
  );
}
