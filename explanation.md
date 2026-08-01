# IABTM — Intended System Design

## Purpose

IABTM (I Am Better Than Me) is a personal growth curator. Its purpose is not
to show a generic collection of popular media. It should remember who a user
is, understand who they want to become, and recommend a small number of media
items that make progress toward that direction.

The intended product loop is:

```text
Account → one-time onboarding → identity + goals → semantic profile
        → relevant media discovery → safety/quality filtering → ranked curation
        → user feedback → improved future recommendations
```

## User journey

### 1. Account creation and sign-in

Users create an account with email and password. The authentication provider
creates a stable user ID. This ID is the key that links every profile field,
goal, interaction, recommendation, and preference to that person.

On subsequent visits, the user signs in and goes directly to their dashboard.
They should never be asked to fill the complete onboarding questionnaire
again unless they explicitly choose to edit their profile.

### 2. One-time onboarding

The onboarding flow collects useful recommendation signals:

- Current-self attributes: where the user feels they are now.
- Imagined-self attributes: the person they want to become.
- Free-text notes: nuance that a fixed list of options cannot capture.
- Learning styles and media preferences.
- Active goals, domains, and time horizon.

This is not just decorative profile data. It is transformed into a semantic
profile, for example:

> “I am building confidence and focused work habits. I want to create a strong
> software design portfolio within six months. I learn best through visual
> breakdowns and practical examples.”

### 3. Persistent data model

In the ideal production system, Supabase PostgreSQL is the source of truth.
Authentication remains in `auth.users`; application tables reference that
authenticated user ID.

Core information to store:

| Area | What is stored |
| --- | --- |
| Profile | Name, profile name, optional image, onboarding state |
| Identity | Current traits, imagined traits, narratives, media preferences |
| Goals | Domain, goal title, timeline, progress, status |
| Content | Normalised YouTube/Pinterest/editorial metadata and quality signals |
| Interactions | Viewed, saved, completed, liked, disliked, not-for-me |
| Recommendations | Ranked snapshots and score explanations |
| Vectors | Embeddings for profile/goals and content |

Row Level Security (RLS) must ensure that a signed-in user can only read and
write their own profile, goals, and interaction history.

## Semantic recommendation system

### Embeddings and pgvector

An embedding converts text into a list of numbers representing its meaning.
Similar meanings have vectors that are close together, even if the exact words
are different.

For example, these can be recognised as related:

```text
User goal:      Build a compelling UX portfolio
Video title:    How designers turn case studies into hiring stories
```

The system creates embeddings for:

1. The user’s identity summary.
2. Each active goal title and domain.
3. Every content item’s title, description, channel/author, tags, and type.

`pgvector` stores these vectors directly in PostgreSQL and performs similarity
search. This keeps transactional user data and semantic search in one managed
database.

### Discovery versus recommendation

These are separate jobs and should stay separate.

| Stage | Responsibility |
| --- | --- |
| Discovery | Ask a provider such as YouTube for candidate videos using a goal-specific query. |
| Normalisation | Store a common title, description, source URL, duration, thumbnail, type, and vector. |
| Quality filter | Reject obvious full uploads, keyword stuffing, irrelevant trends, duplicates, and unembeddable items. |
| Semantic retrieval | Find candidates closest to the user’s active goals and identity vector. |
| Ranking | Blend goal alignment, identity match, quality, freshness, and user feedback. |
| Presentation | Show the recommendation, why it was selected, preview, and open-source action. |

This distinction prevents a broad YouTube search from becoming the final
recommendation feed.

### Goal-aware YouTube queries

The query sent to YouTube must use the actual goal title, not only a broad
category.

Bad:

```text
Knowledge Film
```

Better:

```text
Build a software design portfolio case study breakdown
```

The content type can refine the query, but the goal supplies the meaning.
Additional rules should remove terms and sources that signal poor relevance,
such as “full movie”, “status”, “download”, “viral”, and repeated hashtag
strings when the user asked for educational media.

### Ideal ranking formula

Each candidate receives a transparent score:

```text
final score =
  35% goal alignment
  25% identity alignment
  15% content quality and source trust
  10% user feedback history
  10% freshness
   5% diversity / avoidance of duplicates
```

The exact weights can evolve, but every displayed item should have a concise
reason, such as:

> “Selected because it directly supports your goal to build a software design
> portfolio and matches your preference for practical visual breakdowns.”

### Feedback closes the loop

Feedback is essential. Opening a video means low-confidence interest; saving,
finishing, and liking it are stronger positive signals; “not for me” is a
strong negative signal.

Over time, the curator learns which formats, durations, channels, and goal
angles actually help the individual user. Feedback should update the next
ranking, not merely display a confirmation toast.

## Media experience

### YouTube

- A server-side YouTube API key discovers videos.
- The UI shows a thumbnail, title, duration, description, and domain.
- Eligible videos play in YouTube’s official embedded player.
- “Open source” opens the public YouTube URL in a new tab.

The YouTube API key must stay on the backend. It is never sent to the browser.

### Pinterest

Pinterest is useful for visual Art curation from an authorised board. It is
not a general unrestricted image-search service. Pins should show their image
in the preview dialog and open the original Pin in Pinterest.

### Other media sources

The same normalised content format allows future providers—books, podcasts,
editorials, courses—to participate in the same ranking system.

## Security model

1. Public Supabase URL and publishable key may appear in browser environment
   variables.
2. Supabase secret keys, PostgreSQL URLs, provider client secrets, and OpenAI
   keys stay in server-only environment files or deployment secret managers.
3. Authentication protects browser routes and backend API endpoints validate
   the user token before accepting a user ID.
4. Supabase RLS protects data even if a browser request is forged.
5. Environment files are ignored by Git and must never be committed.

## Deployment-ready outcome

When the system reaches this design, a user can sign in on a new device and
find the same identity, goals, history, and curated feed. The backend pulls
fresh, quality-controlled content, pgvector finds semantically suitable
items, and feedback makes every later recommendation more personal.
