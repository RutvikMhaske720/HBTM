This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.

# HBTM

Backend (FastAPI, from backend/):

cd backend
.venv/bin/uvicorn app.api.main:app --reload --port 8000
Frontend (Next.js, from repo root):

npm run dev
Frontend runs at http://localhost:3000, backend at http://localhost:8000 (already wired via NEXT_PUBLIC_API_URL in .env.local).

## Real data and live curated media

The backend now persists users, goals, identity data, media, and interactions
in `backend/data/iabtm.db` (SQLite). This is a real database and needs no API
key for local development. It is ignored by Git, so each environment keeps its
own data. Start the backend from `backend/` as shown above; it will create the
database and seed the starter catalogue automatically.

To make **Get more like this** return real YouTube results:

1. In Google Cloud Console, create a project and enable **YouTube Data API v3**.
2. Create an API key and restrict it to that API (and to your backend's server/IP when deployed).
3. Copy `backend/env.example` to `backend/.env` and set `YOUTUBE_API_KEY=...`.
4. Restart the FastAPI server. The app never sends this key to the browser.

No key is needed for in-app YouTube previews or the **Open source** button;
the key is only used server-side to discover new videos. Reddit discovery
additionally needs `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, and a descriptive
`REDDIT_USER_AGENT`. `OPENAI_API_KEY` is optional and is only needed if you
choose to replace the local embedding approach with OpenAI embeddings.

Live **Music** first uses Spotify with `SPOTIFY_CLIENT_ID` and
`SPOTIFY_CLIENT_SECRET`, then falls back to YouTube if Spotify is unavailable.
Spotify results use the official embed player and an external Spotify link.

For production, use a managed PostgreSQL instance (for example Supabase,
Neon, or RDS), put its connection URL in the deployment's secret manager, and
add the PostgreSQL adapter/migration before switching `DATABASE_URL`; this
project's current repository is intentionally SQLite-only so it cannot silently
fall back to an unconfigured cloud database.

### Pinterest Art

Pinterest supplies visual Art from a board you authorise; it is not used as a
general web-image search engine. Register and connect a Pinterest developer
app, then set `PINTEREST_BOARD_ID` and either `PINTEREST_ACCESS_TOKEN` or both
`PINTEREST_CLIENT_ID` and `PINTEREST_CLIENT_SECRET` in `backend/.env`. The
necessary Pinterest permissions are `boards:read,pins:read`. After restarting
the backend, select **Art** and choose **Get more like this**. Pins appear with
an in-app image preview and an **Open source** link to Pinterest.
