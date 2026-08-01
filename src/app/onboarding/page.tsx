"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { GoalSuggestion } from "@/lib/api";
import { useIdentityStore } from "@/lib/store/identity.store";
import { useAgentStore } from "@/lib/store/agent.store";

// --- Data -------------------------------------------------------------

const CURRENT_SELF_ATTRS = [
  "Unrelaxed", "Don't Believe In Myself", "Tired", "Lazy", "Absent-minded",
  "Small Faith", "Depressed", "In Debt", "Isolated", "Disconnected",
  "Dreamer", "Time Management", "Busy", "Exhausted", "Perfectionist",
  "Fitness Inconsistency", "Self-conscious", "Out Of Shape", "Burnt Out", "Creatively Stuck",
];

const IMAGINED_SELF_ATTRS = [
  "Confident", "Energetic", "Focused", "Disciplined", "Mindful",
  "Faithful", "Happy", "Wealthy", "Connected", "Present",
  "Healthy", "Active", "Peaceful", "Courageous", "Self-accepting",
  "Action-oriented", "Self-assured", "Imaginative", "Accountable", "Recharged",
];

const LEARNING_STYLES = ["Verbal", "Aural", "Kinesthetic", "Logical", "Social", "Solitary"];

const MEDIA_TYPES = ["Audio", "Video", "Books", "Articles", "Presentation", "Movies", "Podcasts"];

const GOAL_DOMAINS: { label: string; color: string }[] = [
  { label: "Career", color: "#9C7A3A" },
  { label: "Creativity", color: "#C97A3D" },
  { label: "Mindset", color: "#6E5AA0" },
  { label: "Health", color: "#5E8F5A" },
  { label: "Knowledge", color: "#3E5E8C" },
  { label: "Relationships", color: "#A8497A" },
  { label: "Finance", color: "#7A8C4A" },
  { label: "Purpose", color: "#2F6F6B" },
];

const TIMELINES = ["3 months", "6 months", "1 year", "Ongoing"];

const STEP_TITLES = [
  "Go from your current self to the self you imagine",
  "How do you learn best?",
  "Media preferences",
  "Tell us about yourself",
  "What do you want to work on?",
];

const STEP_EYEBROWS = [
  "Starting your paths",
  "Personalizing your journey",
  "Personalizing your journey",
  "Starting your paths",
  "Starting your paths",
];

type FormState = {
  currentSelf: string[];
  imaginedSelf: string[];
  currentSelfNotes: string;
  imaginedSelfNotes: string;
  learningStyles: string[];
  mediaTypes: string[];
  name: string;
  profileName: string;
  email: string;
  phone: string;
  photo: string | null;
  goals: string[];
  goalTitles: Record<string, string>;
  timeline: string | null;
};

const EMPTY_FORM: FormState = {
  currentSelf: [],
  imaginedSelf: [],
  currentSelfNotes: "",
  imaginedSelfNotes: "",
  learningStyles: [],
  mediaTypes: [],
  name: "",
  profileName: "",
  email: "",
  phone: "",
  photo: null,
  goals: [],
  goalTitles: {},
  timeline: null,
};

// --- Shared bits --------------------------------------------------------

function toggleInList(list: string[], value: string, max?: number) {
  if (list.includes(value)) return list.filter((v) => v !== value);
  if (max && list.length >= max) return list;
  return [...list, value];
}

function Pill({
  label,
  active,
  onClick,
  dotColor,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
  dotColor?: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`inline-flex items-center gap-2 rounded-full border px-4 py-2 text-[14px] transition-colors ${
        active
          ? "border-(--color-accent-secondary) bg-(--color-accent-secondary) text-(--color-text-inverse)"
          : "border-(--color-border) bg-(--color-surface) text-(--color-ink-soft) hover:border-(--color-ink-soft)"
      }`}
    >
      {dotColor && (
        <span
          className="h-2 w-2 rounded-full"
          style={{ background: active ? "var(--color-text-inverse)" : dotColor }}
        />
      )}
      {label}
    </button>
  );
}

function SearchBox({ value, onChange, placeholder }: { value: string; onChange: (v: string) => void; placeholder: string }) {
  return (
    <div className="flex items-center gap-2 rounded-full border border-(--color-border) bg-(--color-surface) px-4 py-2.5">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" className="text-(--color-text-tertiary)">
        <circle cx="11" cy="11" r="7" stroke="currentColor" strokeWidth="2" />
        <path d="M21 21l-4.3-4.3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      </svg>
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full bg-transparent text-[14px] outline-none placeholder:text-(--color-text-tertiary)"
      />
    </div>
  );
}

// --- Step 1: Current self / Imagined self --------------------------------

function IdentityStep({ form, setForm }: { form: FormState; setForm: (f: FormState) => void }) {
  const [meQuery, setMeQuery] = useState("");
  const [iAmQuery, setIAmQuery] = useState("");

  const meOptions = CURRENT_SELF_ATTRS.filter((a) => a.toLowerCase().includes(meQuery.toLowerCase()));
  const iAmOptions = IMAGINED_SELF_ATTRS.filter((a) => a.toLowerCase().includes(iAmQuery.toLowerCase()));

  return (
    <div className="grid gap-10 lg:grid-cols-2">
      <div>
        <div className="mb-4 flex items-center gap-3">
          <span className="flex h-10 w-24 items-center justify-center rounded-full bg-(--color-bg-beige) text-sm font-semibold text-(--color-ink)">
            Me
          </span>
          <span className="text-[13px] text-(--color-text-tertiary)">This is your current self</span>
        </div>
        <SearchBox value={meQuery} onChange={setMeQuery} placeholder="Search me..." />
        <div className="mt-4 flex flex-wrap gap-2.5">
          {meOptions.map((attr) => (
            <Pill
              key={attr}
              label={attr}
              active={form.currentSelf.includes(attr)}
              onClick={() => setForm({ ...form, currentSelf: toggleInList(form.currentSelf, attr, 5) })}
            />
          ))}
        </div>
        <textarea
          value={form.currentSelfNotes}
          onChange={(e) => setForm({ ...form, currentSelfNotes: e.target.value })}
          placeholder="Anything else about where you're at right now? (optional)"
          rows={3}
          maxLength={500}
          className="mt-4 w-full rounded-xl border border-(--color-border) bg-(--color-surface) p-3 text-[14px] outline-none placeholder:text-(--color-text-tertiary) focus:ring-2 focus:ring-(--color-accent-secondary)"
        />
      </div>

      <div>
        <div className="mb-4 flex items-center gap-3">
          <span className="flex h-10 w-24 items-center justify-center rounded-full bg-(--color-accent-secondary) text-sm font-semibold text-(--color-text-inverse)">
            I Am
          </span>
          <span className="text-[13px] text-(--color-text-tertiary)">This is your imagined self</span>
        </div>
        <SearchBox value={iAmQuery} onChange={setIAmQuery} placeholder="Search attributes..." />
        <div className="mt-4 flex flex-wrap gap-2.5">
          {iAmOptions.map((attr) => (
            <Pill
              key={attr}
              label={attr}
              active={form.imaginedSelf.includes(attr)}
              onClick={() => setForm({ ...form, imaginedSelf: toggleInList(form.imaginedSelf, attr, 5) })}
            />
          ))}
        </div>
        <textarea
          value={form.imaginedSelfNotes}
          onChange={(e) => setForm({ ...form, imaginedSelfNotes: e.target.value })}
          placeholder="Anything else about who you're becoming? (optional)"
          rows={3}
          maxLength={500}
          className="mt-4 w-full rounded-xl border border-(--color-border) bg-(--color-surface) p-3 text-[14px] outline-none placeholder:text-(--color-text-tertiary) focus:ring-2 focus:ring-(--color-accent-secondary)"
        />
      </div>
    </div>
  );
}

// --- Step 4: Profile info (no password / no auth gate) -------------------

function ProfileStep({ form, setForm }: { form: FormState; setForm: (f: FormState) => void }) {
  return (
    <div className="grid gap-10 lg:grid-cols-[240px_1fr]">
      <div className="flex flex-col items-center gap-3 text-center">
        <label className="flex h-52 w-52 cursor-pointer items-center justify-center rounded-full border-2 border-dashed border-(--color-accent-secondary)/50 bg-(--color-bg-offwhite) overflow-hidden">
          {form.photo ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={form.photo} alt="Profile preview" className="h-full w-full object-cover" />
          ) : (
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" className="text-(--color-accent-secondary)">
              <rect x="3" y="5" width="18" height="14" rx="2" stroke="currentColor" strokeWidth="1.6" />
              <circle cx="9" cy="10.5" r="1.8" stroke="currentColor" strokeWidth="1.6" />
              <path d="M21 16l-5.5-5-4 4-2-1.5L3 18" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          )}
          <input
            type="file"
            accept="image/*"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (!file) return;
              const url = URL.createObjectURL(file);
              setForm({ ...form, photo: url });
            }}
          />
        </label>
        <p className="text-[13px] text-(--color-text-tertiary)">
          Drag&amp;Drop your photo
          <br />
          or select on the device
        </p>
      </div>

      <div className="flex max-w-md flex-col gap-5">
        <Field label="Your name" value={form.name} onChange={(v) => setForm({ ...form, name: v })} />
        <Field label="Profile name" value={form.profileName} onChange={(v) => setForm({ ...form, profileName: v })} />
        <Field label="Your email" type="email" value={form.email} onChange={(v) => setForm({ ...form, email: v })} />
        <Field label="Your phone number" type="tel" value={form.phone} onChange={(v) => setForm({ ...form, phone: v })} />
      </div>
    </div>
  );
}

function Field({
  label,
  value,
  onChange,
  type = "text",
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  type?: string;
}) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-[14px] font-medium text-(--color-ink)">{label}</span>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="h-12 w-full rounded-lg border border-(--color-border) bg-(--color-surface) px-4 text-[15px] outline-none focus:ring-2 focus:ring-(--color-accent-secondary)"
      />
    </label>
  );
}

// --- Step 5: Goals ---------------------------------------------------------

function GoalsStep({ form, setForm }: { form: FormState; setForm: (f: FormState) => void }) {
  const [suggestions, setSuggestions] = useState<Record<string, string>>({});

  useEffect(() => {
    api.getGoalSuggestions()
      .then((list: GoalSuggestion[]) => {
        setSuggestions(Object.fromEntries(list.map((s) => [s.domain, s.suggested_title])));
      })
      .catch(() => {
        // Non-critical — the goal title input just falls back to the domain name.
      });
  }, []);

  return (
    <div>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {GOAL_DOMAINS.map((g) => {
          const active = form.goals.includes(g.label);
          return (
            <button
              key={g.label}
              type="button"
              onClick={() => {
                const nextGoals = toggleInList(form.goals, g.label);
                const turningOn = nextGoals.includes(g.label) && !form.goals.includes(g.label);
                setForm({
                  ...form,
                  goals: nextGoals,
                  goalTitles:
                    turningOn && !form.goalTitles[g.label]
                      ? { ...form.goalTitles, [g.label]: suggestions[g.label] ?? "" }
                      : form.goalTitles,
                });
              }}
              className={`flex flex-col items-start gap-3 rounded-2xl border p-5 text-left transition-colors ${
                active ? "border-(--color-accent-secondary)" : "border-(--color-border) hover:border-(--color-ink-soft)"
              }`}
              style={{ background: active ? `${g.color}26` : "var(--color-surface)" }}
            >
              <span className="h-8 w-8 rounded-full" style={{ background: g.color }} />
              <span className="text-[15px] font-semibold text-(--color-ink)">{g.label}</span>
            </button>
          );
        })}
      </div>

      {form.goals.length > 0 && (
        <div className="mt-8 space-y-3">
          <p className="text-[14px] font-medium text-(--color-ink)">Make it specific (optional)</p>
          {form.goals.map((domain) => (
            <div key={domain} className="flex items-center gap-3">
              <span className="w-28 shrink-0 text-[12px] font-medium text-(--color-text-tertiary)">{domain}</span>
              <input
                value={form.goalTitles[domain] ?? ""}
                onChange={(e) => setForm({ ...form, goalTitles: { ...form.goalTitles, [domain]: e.target.value } })}
                placeholder={suggestions[domain] ?? domain}
                className="h-10 flex-1 rounded-lg border border-(--color-border) bg-(--color-surface) px-3 text-[13px] outline-none focus:ring-2 focus:ring-(--color-accent-secondary)"
              />
            </div>
          ))}
        </div>
      )}

      <p className="mb-3 mt-9 text-[14px] font-medium text-(--color-ink)">By when?</p>
      <div className="flex flex-wrap gap-2.5">
        {TIMELINES.map((t) => (
          <Pill key={t} label={t} active={form.timeline === t} onClick={() => setForm({ ...form, timeline: t })} />
        ))}
      </div>
    </div>
  );
}

// --- Completion reveal ------------------------------------------------------

const SAMPLE_RECS = [
  { title: "The Creative Habit", type: "Book", domain: "Creativity", color: "#C97A3D", why: "Builds on your goal to work on Creativity" },
  { title: "Deep Work — Cal Newport (talk)", type: "Podcast", domain: "Mindset", color: "#6E5AA0", why: "Matches your imagined-self trait: Focused" },
  { title: "Atomic Habits, Ch. 1–3", type: "Article", domain: "Health", color: "#5E8F5A", why: "Addresses your current-self trait: Time Management" },
  { title: "A Short Film About Discipline", type: "Film", domain: "Purpose", color: "#2F6F6B", why: "Aligned with your 6 month timeline" },
  { title: "Studio Ghibli Art Retrospective", type: "Art", domain: "Creativity", color: "#C97A3D", why: "Selected for your Verbal learning style" },
];

function RevealStep({ recs }: { recs: typeof SAMPLE_RECS }) {
  const [thinking, setThinking] = useState(true);
  useMemo(() => {
    const t = setTimeout(() => setThinking(false), 2400);
    return () => clearTimeout(t);
  }, []);

  if (thinking) {
    return (
      <div className="flex flex-col items-center justify-center gap-6 py-24 text-center">
        <span className="relative flex h-20 w-20 items-center justify-center">
          <span className="absolute inset-0 animate-ping rounded-full bg-(--color-accent-secondary)/30" />
          <span className="absolute inset-2 animate-pulse rounded-full bg-(--color-accent-secondary)/50" />
          <span className="relative h-6 w-6 rounded-full bg-(--color-accent-secondary)" />
        </span>
        <p className="text-lg font-medium text-(--color-ink)">
          Your AI Curator is analyzing your profile…
        </p>
        <p className="text-[14px] text-(--color-text-tertiary)">
          Reading identity graph · scoring growth potential · checking safety
        </p>
      </div>
    );
  }

  const displayRecs = recs.length > 0 ? recs : SAMPLE_RECS;

  return (
    <div>
      <p className="text-[14px] text-(--color-text-tertiary)">Curated because it advances the path you just set</p>
      <div className="mt-6 grid gap-5 sm:grid-cols-2 lg:grid-cols-5">
        {displayRecs.slice(0, 5).map((rec, i) => (
          <div
            key={rec.title}
            className="flex flex-col justify-between rounded-2xl border border-(--color-border) bg-(--color-surface) p-4"
            style={{ animation: `fadeInUp 400ms ${i * 90}ms both` }}
          >
            <div>
              <span
                className="inline-block rounded-full px-2.5 py-1 text-[11px] font-medium text-white"
                style={{ background: (rec as { color?: string }).color ?? domainColor(rec.domain) }}
              >
                {rec.domain}
              </span>
              <p className="mt-3 text-[15px] font-semibold leading-snug text-(--color-ink)">{rec.title}</p>
              <p className="mt-1 text-[12px] uppercase tracking-wide text-(--color-text-tertiary)">{(rec as any).type ?? (rec as any).content_type}</p>
            </div>
            <p className="mt-4 text-[12px] text-(--color-text-secondary)">{(rec as any).why ?? (rec as any).why_recommended}</p>
          </div>
        ))}
      </div>
      <div className="mt-10 flex justify-center">
        <Link
          href="/dashboard"
          className="rounded-full bg-(--color-accent-secondary) px-8 py-3.5 text-[15px] font-medium text-(--color-text-inverse) transition-transform hover:-translate-y-0.5"
        >
          Enter your dashboard
        </Link>
      </div>
      <style>{`
        @keyframes fadeInUp { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
      `}</style>
    </div>
  );
}

const DOMAIN_COLORS: Record<string, string> = {
  Creativity: "#C97A3D",
  Mindset: "#6E5AA0",
  Health: "#5E8F5A",
  Knowledge: "#3E5E8C",
  Career: "#9C7A3A",
  Relationships: "#A8497A",
  Finance: "#7A8C4A",
  Purpose: "#2F6F6B",
};
function domainColor(domain: string): string {
  return DOMAIN_COLORS[domain] ?? "#8a8a8a";
}

// --- Wizard shell -----------------------------------------------------------

export default function OnboardingPage() {
  const [step, setStep] = useState(0);
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [revealed, setRevealed] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [apiRecs, setApiRecs] = useState<typeof SAMPLE_RECS>([]);
  const router = useRouter();
  const setUserId = useIdentityStore((s) => s.setUserId);
  const setProfile = useIdentityStore((s) => s.setProfile);
  const setOnboardingComplete = useIdentityStore((s) => s.setOnboardingComplete);
  const setAgentStatus = useAgentStore((s) => s.setAgentStatus);
  const setRunId = useAgentStore((s) => s.setRunId);

  const totalSteps = 5;

  const isValid = useMemo(() => {
    switch (step) {
      case 0:
        return form.currentSelf.length > 0 && form.imaginedSelf.length > 0;
      case 1:
        return form.learningStyles.length > 0;
      case 2:
        return form.mediaTypes.length > 0;
      case 3:
        return form.name.trim().length > 0 && form.email.trim().length > 0;
      case 4:
        return form.goals.length > 0 && !!form.timeline;
      default:
        return false;
    }
  }, [step, form]);

  async function handleContinue() {
    if (step < totalSteps - 1) {
      setStep((s) => s + 1);
      return;
    }

    // Last step — submit to backend
    setSubmitting(true);
    setSubmitError(null);
    try {
      const payload = {
        name: form.name,
        profile_name: form.profileName,
        email: form.email,
        phone: form.phone,
        current_self: form.currentSelf,
        imagined_self: form.imaginedSelf,
        current_self_notes: form.currentSelfNotes,
        imagined_self_notes: form.imaginedSelfNotes,
        goals: form.goals.map((domain) => form.goalTitles[domain]?.trim() || domain),
        goal_domains: form.goals,
        timeline: form.timeline ?? "Ongoing",
        learning_styles: form.learningStyles,
        media_types: form.mediaTypes,
      };

      const result = await api.onboardUser(payload);
      setUserId(result.user_id);
      setProfile({ userId: result.user_id, name: result.name });
      setOnboardingComplete(true);
      setRevealed(true);

      // Trigger agent run
      const runResult = await api.triggerAgentRun(result.user_id);
      setRunId(runResult.run_id);
      setAgentStatus("running");

      // Fetch first recommendations (may wait for agent run)
      const recs = await api.getRecommendations(result.user_id);
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      setApiRecs(recs as any);
    } catch (err) {
      console.error("Onboarding API error:", err);
      setSubmitError(
        "Couldn't reach the server. Make sure the backend is running, then try again."
      );
    } finally {
      setSubmitting(false);
    }
  }

  if (revealed) {
    return (
      <main className="min-h-screen bg-(--color-bg-primary) px-6 py-16 lg:px-10">
        <div className="mx-auto max-w-5xl">
          <RevealStep recs={apiRecs} />
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-(--color-bg-primary) px-6 py-10 lg:px-10">
      <div className="mx-auto max-w-5xl">
        <Link href="/" className="font-display text-xl font-semibold tracking-tight text-(--color-ink)">
          IABTM
        </Link>

        <div className="mt-8 flex items-center gap-4">
          <div className="h-1 flex-1 rounded-full bg-(--color-border-subtle)">
            <div
              className="h-1 rounded-full bg-(--color-accent-secondary) transition-all duration-500"
              style={{ width: `${((step + 1) / totalSteps) * 100}%` }}
            />
          </div>
          <span className="text-[13px] text-(--color-text-tertiary)">
            {step + 1}/{totalSteps}
          </span>
        </div>

        <div className="mt-10">
          <p className="text-[13px] font-medium uppercase tracking-wide text-(--color-text-tertiary)">
            {STEP_EYEBROWS[step]}
          </p>
          <h1 className="mt-2 max-w-2xl text-3xl font-bold tracking-tight text-(--color-ink) sm:text-4xl">
            {STEP_TITLES[step]}
          </h1>
        </div>

        <div className="mt-10">
          {step === 0 && <IdentityStep form={form} setForm={setForm} />}
          {step === 1 && (
            <div className="flex flex-wrap gap-2.5">
              {LEARNING_STYLES.map((s) => (
                <Pill
                  key={s}
                  label={s}
                  active={form.learningStyles.includes(s)}
                  onClick={() => setForm({ ...form, learningStyles: toggleInList(form.learningStyles, s) })}
                />
              ))}
            </div>
          )}
          {step === 2 && (
            <div className="flex flex-wrap gap-2.5">
              {MEDIA_TYPES.map((m) => (
                <Pill
                  key={m}
                  label={m}
                  active={form.mediaTypes.includes(m)}
                  onClick={() => setForm({ ...form, mediaTypes: toggleInList(form.mediaTypes, m) })}
                />
              ))}
            </div>
          )}
          {step === 3 && <ProfileStep form={form} setForm={setForm} />}
          {step === 4 && <GoalsStep form={form} setForm={setForm} />}
        </div>

        {submitError && (
          <p className="mt-6 rounded-lg bg-(--color-status-error-bg) px-4 py-3 text-[13px] text-(--color-status-error-text)">
            {submitError}
          </p>
        )}

        <div className="mt-14 flex items-center gap-4">
          <button
            type="button"
            onClick={() => setStep((s) => Math.max(0, s - 1))}
            disabled={step === 0}
            className="rounded-full border border-(--color-border) px-7 py-3 text-[15px] font-medium text-(--color-ink) disabled:opacity-40"
          >
            Back
          </button>
          <button
            type="button"
            onClick={handleContinue}
            disabled={!isValid || submitting}
            className="rounded-full bg-(--color-accent-secondary) px-7 py-3 text-[15px] font-medium text-(--color-text-inverse) transition-opacity disabled:opacity-30"
          >
            {submitting ? "Processing…" : "Continue"}
          </button>
        </div>
      </div>
    </main>
  );
}
