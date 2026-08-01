"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { supabase } from "@/lib/supabase";

type Mode = "sign-in" | "sign-up";

export default function AuthPage() {
  const [mode, setMode] = useState<Mode>("sign-in");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [message, setMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const router = useRouter();

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("");
    setSubmitting(true);
    try {
      if (mode === "sign-up") {
        const { data, error } = await supabase.auth.signUp({
          email,
          password,
          options: { data: { full_name: name }, emailRedirectTo: `${window.location.origin}/auth` },
        });
        if (error) throw error;
        if (!data.session) {
          setMessage("Check your inbox to confirm your account, then sign in.");
        } else {
          router.replace("/onboarding");
        }
      } else {
        const { error } = await supabase.auth.signInWithPassword({ email, password });
        if (error) throw error;
        router.replace("/dashboard");
      }
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Something went wrong. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="theme-landing flex min-h-screen items-center justify-center bg-(--color-bg-primary) px-5 py-12">
      <section className="w-full max-w-md rounded-3xl border border-(--color-border) bg-(--color-surface) p-8 shadow-xl">
        <Link href="/" className="font-display text-2xl font-semibold text-(--color-ink)">IABTM</Link>
        <p className="mt-6 text-xs font-medium uppercase tracking-[0.2em] text-(--color-text-tertiary)">Your personal curator</p>
        <h1 className="mt-2 text-3xl font-bold text-(--color-ink)">{mode === "sign-in" ? "Welcome back" : "Create your account"}</h1>
        <p className="mt-2 text-sm text-(--color-text-secondary)">{mode === "sign-in" ? "Continue where your growth path left off." : "Your profile and recommendations stay with your account."}</p>

        <form onSubmit={submit} className="mt-7 space-y-4">
          {mode === "sign-up" && <label className="block text-sm font-medium text-(--color-ink)">Name<input required value={name} onChange={(event) => setName(event.target.value)} className="mt-1.5 w-full rounded-xl border border-(--color-border) px-3 py-2.5 outline-none focus:ring-2 focus:ring-(--color-accent-secondary)" /></label>}
          <label className="block text-sm font-medium text-(--color-ink)">Email<input required type="email" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} className="mt-1.5 w-full rounded-xl border border-(--color-border) px-3 py-2.5 outline-none focus:ring-2 focus:ring-(--color-accent-secondary)" /></label>
          <label className="block text-sm font-medium text-(--color-ink)">Password<input required minLength={8} type="password" autoComplete={mode === "sign-in" ? "current-password" : "new-password"} value={password} onChange={(event) => setPassword(event.target.value)} className="mt-1.5 w-full rounded-xl border border-(--color-border) px-3 py-2.5 outline-none focus:ring-2 focus:ring-(--color-accent-secondary)" /></label>
          {message && <p role="alert" className="rounded-xl bg-(--color-bg-offwhite) px-3 py-2 text-sm text-(--color-text-secondary)">{message}</p>}
          <button disabled={submitting} className="w-full rounded-full bg-(--color-accent-secondary) px-5 py-3 text-sm font-semibold text-(--color-text-inverse) disabled:opacity-50">{submitting ? "Please wait…" : mode === "sign-in" ? "Sign in" : "Create account"}</button>
        </form>

        <button onClick={() => { setMode(mode === "sign-in" ? "sign-up" : "sign-in"); setMessage(""); }} className="mt-5 w-full text-sm text-(--color-accent-secondary)">
          {mode === "sign-in" ? "New here? Create an account" : "Already have an account? Sign in"}
        </button>
      </section>
    </main>
  );
}
