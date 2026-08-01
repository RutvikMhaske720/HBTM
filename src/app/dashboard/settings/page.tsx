"use client";

import { useIdentityStore } from "@/lib/store/identity.store";

export default function SettingsPage() {
  const profile = useIdentityStore((s) => s.profile);
  const userId = useIdentityStore((s) => s.userId);
  const clear = useIdentityStore((s) => s.clear);

  return (
    <div className="max-w-2xl space-y-8">
      <div>
        <p className="text-[13px] uppercase tracking-widest text-(--color-text-tertiary)">Account</p>
        <h1 className="mt-1 text-3xl font-bold tracking-tight text-(--color-ink)">Settings</h1>
      </div>

      {/* Profile section */}
      <section className="rounded-2xl border border-(--color-border) bg-(--color-surface) p-6 space-y-4">
        <h2 className="text-[15px] font-semibold text-(--color-ink)">Profile</h2>
        <div className="space-y-3 text-[14px]">
          <div className="flex justify-between border-b border-(--color-border-subtle) pb-3">
            <span className="text-(--color-text-tertiary)">Name</span>
            <span className="text-(--color-ink)">{profile?.name ?? "—"}</span>
          </div>
          <div className="flex justify-between border-b border-(--color-border-subtle) pb-3">
            <span className="text-(--color-text-tertiary)">User ID</span>
            <span className="font-mono text-[12px] text-(--color-text-secondary)">{userId}</span>
          </div>
        </div>
      </section>

      {/* AI Mode section */}
      <section className="rounded-2xl border border-(--color-border) bg-(--color-surface) p-6 space-y-4">
        <h2 className="text-[15px] font-semibold text-(--color-ink)">AI Mode</h2>
        <div className="grid grid-cols-3 gap-3">
          {["Cloud", "Hybrid", "Local"].map((mode, i) => (
            <button
              key={mode}
              disabled={i > 0}
              className={`rounded-xl border p-4 text-left text-[13px] transition-colors ${
                i === 0
                  ? "border-(--color-accent-secondary) bg-(--color-accent-secondary)/10"
                  : "border-(--color-border) opacity-50"
              }`}
            >
              <p className="font-semibold text-(--color-ink)">{mode}</p>
              <p className="mt-0.5 text-[11px] text-(--color-text-tertiary)">
                {i === 0 ? "Active" : "Coming soon"}
              </p>
            </button>
          ))}
        </div>
      </section>

      {/* Danger zone */}
      <section className="rounded-2xl border border-(--color-accent-focus)/40 bg-(--color-status-error-bg) p-6 space-y-3">
        <h2 className="text-[15px] font-semibold text-(--color-status-error-text)">Danger Zone</h2>
        <p className="text-[13px] text-(--color-status-error-text)">
          Clearing your session will remove your user ID from this device. Your data remains in the backend.
        </p>
        <button
          onClick={() => {
            if (confirm("Clear local session?")) clear();
          }}
          className="rounded-full bg-(--color-accent-focus) px-5 py-2.5 text-[13px] font-medium text-(--color-ink) hover:brightness-110"
        >
          Clear Session
        </button>
      </section>
    </div>
  );
}
