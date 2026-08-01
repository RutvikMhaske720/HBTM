# IABTM — Current State, Caveats, and Path to the Intended Design

This document describes the repository as it currently exists. It is the
practical companion to `explanation.md`: use it to identify what is complete,
what is only prepared, and what must be fixed next.

## Current implementation snapshot

| Area | Current status | Notes |
| --- | --- | --- |
| Frontend account page | Implemented | `/auth` uses Supabase email/password sign-up and sign-in. |
| Dashboard guard | Implemented | A missing browser session redirects to `/auth`. |
| Returning user behaviour | Partially implemented | The dashboard checks for a stored API profile; existing users bypass onboarding. |
| Authenticated user ID | Implemented | Onboarding sends the Supabase user ID to the backend as `user_id`. |
| Sign out | Implemented | The dashboard avatar signs out. |
| SQLite persistence | Working | Existing prototype data migrates from legacy JSON into `backend/data/iabtm.db`. |
| PostgreSQL repository | Implemented, not live-verified | The backend now has a PostgreSQL JSONB record store using `psycopg`. |
| pgvector repository | Implemented, not live-verified | `vector_records` uses `vector(64)` and cosine HNSW search. |
| Supabase connection | Blocked | The current supplied Direct connection hostname did not resolve from the development environment. |
| Local semantic embeddings | Working | TF-IDF + SVD provides 64-dimensional vectors without another API key. |
| Hosted semantic embeddings | Not implemented | There is no active OpenAI embedding client yet. |
| YouTube discovery | Working and live-verified | Uses the backend YouTube API key. |
| Music | Resilient | Spotify is attempted first; a Spotify account-policy error falls back to YouTube. |
| Pinterest Art | Prepared | Requires Pinterest credentials and an authorised board ID. |

## Important immediate caveat: database connection

The backend was switched from SQLite to a PostgreSQL `DATABASE_URL`, but the
provided Direct connection host failed DNS resolution during a real connection
test. This prevents automatic creation of the PostgreSQL `records` and
`vector_records` tables.

### Required fix

Use the exact **Session Pooler** URI from Supabase:

1. Supabase Dashboard → **Connect**.
2. Select **Session pooler**.
3. Select **URI**.
4. Replace the `DATABASE_URL=` value in `backend/.env` with that URI.
5. Replace `[YOUR-PASSWORD]` locally; do not send it through chat or commit it.

The expected shape is:

```env
DATABASE_URL=postgresql://postgres.PROJECT_REF:YOUR_PASSWORD@REGION.pooler.supabase.com:5432/postgres
```

After this is fixed, restart the backend. The repository code will create the
record table, pgvector extension, and vector table automatically.

## Authentication caveats

### What works now

- A user can create a Supabase email/password account.
- A browser session protects dashboard navigation.
- A user who has already completed backend onboarding is returned to the
  dashboard instead of asked to complete the wizard again.

### What still needs work before production

1. **Backend JWT validation** — current backend endpoints still accept a
   `user_id` supplied by the client. A malicious caller could submit another
   user ID directly to the API. Add a FastAPI dependency that validates the
   Supabase access token and derives the user ID from it.
2. **Supabase RLS tables** — current PostgreSQL storage uses a generic JSONB
   `records` table. It is a valid persistence bridge but does not yet use
   user-owned relational tables and Row Level Security policies.
3. **Email configuration** — Supabase email confirmation should be configured
   with correct Site URL, Redirect URLs, and custom SMTP before production.
4. **Server-side session handling** — browser-only Supabase sessions are good
   for this local prototype. For a production Next.js application, move to
   Supabase SSR/cookie helpers and middleware.

## Recommendation caveats

### Improvement already made

The Curated Media “Get more like this” request now sends the signed-in user
ID. The backend reads that user’s active goal titles and includes them in the
YouTube discovery query. This replaces the earlier generic pattern such as
`Knowledge Film`.

### Why results can still be poor

1. The current discovery query remains a simple text query; it does not yet
   use the vector nearest-neighbour results to generate or rerank the query.
2. YouTube metadata itself can be noisy. An API result may still have a
   keyword-stuffed title, generic film upload, weak description, or misleading
   thumbnail.
3. The local TF-IDF/SVD embedder is a useful no-cost fallback, but it is much
   weaker than a modern semantic embedding model.
4. The current quality/safety filtering does not yet reject enough categories
   of poor YouTube content before displaying it.

### Ordered fixes for high-quality recommendations

1. Establish the live Session Pooler connection and verify pgvector writes.
2. Migrate from generic JSONB records to typed relational tables with RLS.
3. Add backend JWT verification.
4. Ingest YouTube candidates with title, channel, description, tags, duration,
   publication date, and source quality metadata.
5. Add deterministic quality filters, including blocked phrases, duplicate
   detection, duration rules, and channel/source allow/deny lists.
6. Store every candidate vector in pgvector.
7. Query pgvector with a combined identity + active-goal vector and rank only
   those semantic candidates.
8. Add user feedback weighting, diversity constraints, and an evaluation set
   of expected recommendations for known profiles.
9. Optionally replace local embeddings with a hosted semantic embedding model.

## Data migration caveat

The SQLite backend automatically imported existing legacy JSON data. The new
PostgreSQL backend intentionally does not copy SQLite data automatically yet.
Do not delete `backend/data/iabtm.db` or the JSON files. After the Supabase
connection works, create a one-time, reviewed migration script that copies
only the records you want to preserve.

## Environment-variable inventory

Never commit real values. These names are expected:

| File | Variables | Purpose |
| --- | --- | --- |
| Root `.env.local` | `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` | Browser API and Supabase authentication client. |
| `backend/.env` | `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_SECRET_KEY` | Server-only database and Supabase configuration. |
| `backend/.env` | `YOUTUBE_API_KEY` | Server-side YouTube discovery. |
| `backend/.env` | Pinterest variables | Optional board-based Art ingestion. |
| `backend/.env` | Spotify variables | Optional Music discovery; currently falls back to YouTube when Spotify blocks the app. |

## Verification commands

Run these after correcting the database URI:

```bash
cd backend
.venv/bin/uvicorn app.api.main:app --reload --port 8000
```

In another terminal:

```bash
npm run dev
```

Then verify:

1. Create a new account at `/auth`.
2. Complete onboarding once.
3. Sign out and sign in again; dashboard should open without onboarding.
4. Select Curated Media → choose a type → **Get more like this**.
5. Confirm the query and results align with the user’s goal title.
6. Confirm backend logs show a Postgres connection and pgvector table setup.

## Definition of done

This project is ready for the intended behaviour only when all of these are
true:

- Session Pooler database connection succeeds.
- PostgreSQL holds the data after a backend restart.
- pgvector stores and searches content embeddings.
- Backend verifies Supabase user tokens.
- Users can sign in on a second browser and recover their profile/goals.
- Media candidates are filtered and semantically ranked against active goals.
- Recommendation explanations accurately state why a specific item was chosen.
