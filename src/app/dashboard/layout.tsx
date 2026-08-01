"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useIdentityStore } from "@/lib/store/identity.store";
import Sidebar from "@/components/layout/Sidebar";
import TopNav from "@/components/layout/TopNav";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const userId = useIdentityStore((s) => s.userId);
  const router = useRouter();

  useEffect(() => {
    if (!userId) {
      router.replace("/onboarding");
    }
  }, [userId, router]);

  if (!userId) return null;

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
