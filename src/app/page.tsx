import Navbar from "@/components/Navbar";
import InteractiveHero from "@/components/landing/InteractiveHero";
import StatsStrip from "@/components/landing/StatsStrip";
import StepCard from "@/components/landing/StepCard";
import Reveal from "@/components/landing/Reveal";
import MagneticButton from "@/components/landing/MagneticButton";

const STEPS = [
  {
    title: "Profile",
    body: "Tell us who you are today and who you're becoming — no dropdowns, just honest self-selection.",
    accent: "var(--color-accent-secondary)",
  },
  {
    title: "Curate",
    body: "Your AI Curator reads your identity graph and assembles a growth-scored path across film, music, art, and ideas.",
    accent: "var(--color-accent-tertiary)",
  },
  {
    title: "Become",
    body: "Every recommendation moves you toward the self you imagined — not toward another hour of scrolling.",
    accent: "var(--color-accent-warm)",
  },
];

export default function Home() {
  return (
    <>
      <Navbar />
      <main className="flex-1 bg-(--color-bg-primary)">
        <InteractiveHero>
          <p className="mb-5 text-xs font-medium uppercase tracking-[0.3em] text-white/60">
            Your AI growth companion
          </p>
          <h1 className="max-w-3xl text-5xl font-extrabold tracking-tight text-(--color-bg-offwhite) sm:text-6xl lg:text-7xl">
            I am better than me
          </h1>
          <p className="mx-auto mt-6 max-w-md text-lg text-white/70">
            Become the self you imagine. One AI-curated recommendation at a
            time.
          </p>
        </InteractiveHero>

        <StatsStrip />

        <section
          id="how-it-works"
          className="mx-auto max-w-6xl px-6 py-24 lg:px-10"
        >
          <Reveal>
            <p className="text-xs font-medium uppercase tracking-[0.3em] text-(--color-text-tertiary)">
              How it works
            </p>
            <h2 className="mt-3 max-w-xl text-3xl font-bold tracking-tight text-(--color-ink) sm:text-4xl">
              From your current self to the self you imagine.
            </h2>
          </Reveal>

          <div className="mt-14 grid gap-10 sm:grid-cols-3">
            {STEPS.map((step, i) => (
              <StepCard
                key={step.title}
                index={i}
                title={step.title}
                body={step.body}
                accent={step.accent}
              />
            ))}
          </div>
        </section>

        <section className="mx-auto max-w-6xl px-6 pb-28 lg:px-10">
          <Reveal>
            <div className="flex flex-col items-center gap-6 rounded-3xl bg-(--color-bg-beige) px-8 py-16 text-center">
              <span className="inline-flex h-14 w-14 items-center justify-center rounded-full bg-(--color-ink)">
                <span className="h-3 w-3 animate-pulse rounded-full bg-(--color-accent-tertiary)" />
              </span>
              <h2 className="max-w-lg text-3xl font-bold tracking-tight text-(--color-ink)">
                Meet your AI Curator
              </h2>
              <p className="max-w-md text-[15px] text-(--color-text-secondary)">
                An always-on companion that understands who you are, who you
                want to become, and exactly what to put in front of you next.
              </p>
              <MagneticButton
                href="/onboarding"
                className="mt-2 inline-block rounded-full bg-(--color-ink) px-7 py-3.5 text-[15px] font-medium text-(--color-text-inverse) transition-transform hover:-translate-y-0.5"
              >
                Let&apos;s grow
              </MagneticButton>
            </div>
          </Reveal>
        </section>
      </main>
    </>
  );
}
