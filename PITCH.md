# IABTM — 5-Minute Pitch Script

**Format:** hackathon / project judging panel · ~5 min · live demo
**Delivery:** ~130 wpm. Everything in *italics* is a stage direction, not spoken.

---

## Pre-flight checklist (do this 10 minutes before you present)

- [ ] Backend up: `cd backend && .venv/bin/uvicorn app.api.main:app --reload --port 8000`
- [ ] Frontend up: `npm run dev` → http://localhost:3000
- [ ] **Warm the cache**: run one full "Get more like this" on the demo account so the network calls are already made once. Live provider fan-out is the only thing that can make you look slow.
- [ ] Demo account already onboarded, with **at least one specific goal** (e.g. "Build a software design portfolio", domain: Career). A vague goal produces vague results — the specificity *is* the demo.
- [ ] Some feedback history on the account (a few thumbs-up, one "not for me") so the feedback signal isn't cold.
- [ ] Tabs open in this order: `/` (landing) · `/dashboard` · `/dashboard/library` · `/dashboard/identity` · `/dashboard/agent-lab`
- [ ] Backend terminal visible on a second screen if you have one — live logs are free credibility.
- [ ] Screenshots of the library grid + agent trace saved locally as your demo-failure fallback.
- [ ] Zoom browser to 110–125%. Judges are looking at a projector from 4 metres away.

---

## THE SCRIPT

### 0:00 – 0:25 — Hook

> Every recommendation engine you use today is built to answer one question: *what will keep this person watching?*
>
> They're extremely good at it. YouTube knows what you'll click at 1 a.m. Instagram knows exactly which reel holds you for another eight seconds.
>
> But not one of them is built to answer the question people actually care about: **what should I watch to become the person I'm trying to become?**

*Pause. Let that land for a beat.*

> That's the gap we built IABTM for. It stands for **I Am Better Than Me**.

---

### 0:25 – 1:00 — Problem

> Here's the real problem. Engagement algorithms optimise for **who you already are**. They model your past behaviour and give you more of it. That's a feedback loop that makes you more of your current self.
>
> Growth is the opposite motion. It needs content aimed at the gap between who you are now and who you want to be — and that content is often *not* what you'd click on impulse.
>
> So today people do this manually. They screenshot book recommendations, bookmark 40 tabs, save podcast episodes they never open. The curation work is entirely on the human, and it doesn't survive a busy week.
>
> **IABTM automates that curation, and aims it at your goals instead of your attention span.**

---

### 1:00 – 1:20 — What it is

> IABTM is an agentic AI curator. You tell it who you are now, who you want to become, and what you're working toward. Then a pipeline of ten specialised agents goes out across the real internet — YouTube, Spotify, Open Library, podcast catalogues, editorial publishers, open-licensed art — filters hard for quality and relevance, and returns a **small** number of items with a stated reason for each one.
>
> Not a feed. A shortlist you can actually finish.

---

### 1:20 – 3:15 — LIVE DEMO (the centrepiece — do not rush this)

*Switch to the browser. `/dashboard`.*

> This is a real account. During onboarding it captured two things most systems never ask for: my **current self** and my **imagined self** — separately.

*Click **Identity**.*

> That becomes this: an identity graph. Present traits on one side, aspirational traits on the other, plus my learning style and media preferences. This whole thing gets compiled into a single semantic vector — that's what search is actually run against, not keywords.

*Click **Curated Media** (`/dashboard/library`). Pick a content type. Click **Get more like this**.*

> Now watch what it does with a goal. My active goal is "build a software design portfolio."
>
> A naive system searches the category — it sends the word "Career" to YouTube and gets motivational garbage back. **IABTM builds the query from the goal itself**, per medium. For video it searches the goal. For music, it doesn't look for songs *about* my goal — it looks for something to focus *to*. For books it hits Open Library, for podcasts the iTunes catalogue, for essays it goes to actual publishers' feeds — Quanta, Aeon, First Round Review — not the open SEO web.

*Results land. Point at a card.*

> Every candidate that came back had to survive **five gates**, cheapest first. Real title and working link. Published recently. Then the gate that matters — **relevance to my profile**, scored as a blend of vector similarity and literal overlap with my own goal language. Then novelty, so it isn't a near-duplicate of something already in my library. Then reachability — we actually fetch the link and the preview image to prove they resolve.
>
> Anything rejected is **counted by reason**. If this comes back empty, we can tell you exactly why it came back empty. That sounds small. It's the difference between a demo and a system.

*Click into an item — the preview modal.*

> Preview in-app, or open the original source. And this — *point at the "why this" copy* — is the part I care about most. Every single item states why it was selected. **Thirty per cent** goal alignment, **twenty-five** identity match, **twenty-five** growth potential, then recency and my own feedback history — multiplied by a safety factor. No black box. You can argue with the score.

*Click thumbs-up on one item, "not for me" on another.*

> And this closes the loop. That's not a toast notification — it re-weights the next ranking for this domain.

*Navigate to `/dashboard/agent-lab` (type the URL — it's not in the sidebar).*

> Last thing, and this is our favourite. This is the Agent Lab — the live trace of the run that just happened. Memory, Identity, Goal, Content Retrieval, Recommendation, Safety, Evaluation, Output, Notification. Streamed over server-sent events as it executes, with the input and output of every agent.
>
> You are looking at the reasoning, not a summary of the reasoning.

---

### 3:15 – 4:15 — Under the hood

*Switch to architecture slide, or just talk over the Agent Lab screen.*

> Architecture, quickly. Next.js 16 front end. FastAPI backend. The orchestration is **LangGraph** — and the graph *is* the orchestrator: the routing rules are real conditional edges, not prompt instructions.
>
> Two of those edges are the interesting ones. **If the Safety Agent rejects the majority of a batch, the graph loops back to content retrieval and fetches again** — capped at one retry so it can never spin. And **if the Evaluation Agent's confidence is low, the run is routed to human approval instead of straight to output.** The system knows when it doesn't know.
>
> The Safety Agent is a scoring gate, not a keyword blocklist. Dead link, missing preview, engagement-bait title, growth score under threshold — those are hard failures, dropped. Insecure source or unverifiable claim language — *"cure", "overnight", "guaranteed"* — those are soft signals that survive but get ranked down.
>
> Data layer is Supabase Postgres with **pgvector** for similarity search, so transactional user data and semantic search live in one database. Embeddings run locally — TF-IDF plus SVD — which means the semantic layer costs us nothing per query and has no external dependency.
>
> Content comes in through twelve tool adapters behind one normalised format, fanned out concurrently. One dead provider cannot take down a run. Adding a thirteenth source is one adapter file — it inherits the entire filter, scoring and safety stack for free.

*If you have the Chrome extension to show — 15 seconds, otherwise skip:*

> And we built a Chrome extension that feeds real browsing behaviour back in as a growth signal — because what you *actually* do all day is better data than what you told us during onboarding.

---

### 4:15 – 4:45 — Why this is hard, and what's next

> The hard part of this project was never calling APIs. It was this: **the moment your content pool is the real internet instead of a hand-curated seed list, quality control becomes the entire product.** Anyone can wire up a YouTube search in an afternoon. Keeping the garbage out of the results is where the work is — and that's what the five gates, the safety multiplier and the rejection accounting exist to do.
>
> What's next, honestly: hardening auth so the backend derives user identity from a verified token rather than trusting the client, moving to typed tables with row-level security, and swapping the local embedder for a hosted model to sharpen semantic matching.

---

### 4:45 – 5:00 — Close

> Recommendation engines spent fifteen years getting very good at holding your attention.
>
> We think the same machinery — agents, embeddings, semantic retrieval — can be pointed at something better: **helping someone close the gap between who they are and who they're trying to be.**
>
> That's IABTM. Thank you.

*Stop talking. Don't fill the silence. Let them ask.*

---

## Fallback lines (memorise these — you will need one)

| If this happens | Say this, keep moving |
| --- | --- |
| Curation call is slow | "This is fanning out to seven live providers concurrently right now — it's real network latency, not a loading spinner. While it works, let me show you what it's filtering *for*." *→ narrate the five gates* |
| Zero results come back | "Perfect, actually — this is the honesty feature. The rejection report tells us exactly which gate killed everything. That's a *tunable* empty result, not a broken one." |
| A result looks weak / off-topic | "Good catch, and I'll own it — the local embedder is our cost-free fallback and it's the weakest link in the chain. That specific fix is a hosted embedding model, one file." *Don't defend a bad result. Judges respect the diagnosis more than the excuse.* |
| Backend is down | "I'll walk it on screenshots — the flow is identical." *→ open your saved screenshots, keep the same narration* |
| A page throws an error | Do not debug on stage. "That's a UI state bug, not a pipeline one — the API returned fine." Move to the next tab. |
| You're at 4:00 and only halfway | Cut the architecture section to two sentences: *"LangGraph orchestration, ten agents, pgvector search, twelve sources behind one interface."* Then jump straight to the close. **Never cut the close.** |

---

## Q&A prep

**"How is this different from YouTube recommendations?"**
> Objective function. Theirs maximises watch time using your past behaviour. Ours maximises alignment with a goal you explicitly declared — and it will happily recommend something you wouldn't have clicked on your own. That's a feature, not a bug.

**"What stops it recommending harmful self-help content?"**
> A dedicated Safety Agent between ranking and output. Hard drops for bait titles, dead links and sub-threshold growth scores; soft downranking for unverifiable claim language. And if it rejects most of a batch, the graph refetches rather than showing you the least-bad option.

**"Why ten agents? Isn't one LLM call enough?"**
> Because separation is what makes it debuggable and safe. Retrieval, ranking and safety having distinct interfaces is exactly what lets us loop back on a failed safety check and route low-confidence runs to a human. One monolithic call gives you no seam to intervene at. Agent Lab is the proof — you can see each stage's actual input and output.

**"Does it work with no data — cold start?"**
> Yes, degraded and explicitly so. Feedback defaults to a neutral 0.5 prior, and it falls back to domain-level queries. The onboarding questionnaire exists precisely so we're not starting from zero.

**"How do you evaluate recommendation quality?"**
> Right now: the rejection report plus the score breakdown per item, which makes bad output diagnosable. What we don't have yet is a labelled evaluation set — known profiles with expected recommendations — and that's the honest next step.

**"Is the data secure?"**
> Provider keys are server-side only and never reach the browser; the YouTube key is a good example. Auth is Supabase. The gap I'll name for you: the backend currently trusts a client-supplied user ID, so token verification and row-level security are the top of our hardening list.

**"What's the business model?"** *(if it's that kind of judging panel)*
> Subscription for individuals. The stronger wedge is B2B — the same curation pipeline pointed at an organisation's L&D goals, which is a budget that already exists.

---

## Don't say these

Nothing in the script above overclaims, and it should stay that way. Specifically, **don't** say:

- "fully deployed" / "in production" — it runs locally
- "secure and production-ready auth" — token verification isn't in yet, and the script already names that honestly
- user numbers, accuracy percentages, or benchmark figures you can't show on screen

Judges forgive an unfinished edge. They do not forgive a claim they can disprove with one question.

---

## One-line version (for the hallway, the form field, the booth)

> IABTM is an agentic AI curator that recommends media based on who you're trying to become instead of what you'll click — ten LangGraph agents fan out across twelve real sources, filter hard for quality, and show you exactly why each item was chosen.

---

## Minimum slide deck (5 slides — anything more competes with your demo)

1. **Title** — IABTM · *I Am Better Than Me* · one-line description
2. **Problem** — "Engagement algorithms optimise for who you already are." One visual: engagement loop vs growth arc
3. **Live demo** — a blank slide with the logo, so nothing competes with the screen share
4. **Architecture** — the 10-node graph, with the safety loop-back and human-approval branches drawn as real arrows. This is your most impressive slide; make it clean.
5. **Scoring + honesty** — the weight breakdown (30/25/25/10/10) and the five gates. Ends on the close line.
