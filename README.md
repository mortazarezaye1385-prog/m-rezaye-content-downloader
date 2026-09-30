<p align="center"><img src="frontend/public/icon-192.png" width="72" alt="M.R logo" /></p>

# M.Rezaye Content Downloader

A personal, mobile-first web app for downloading media **you are authorized to download** from Instagram, TikTok and YouTube, in the highest quality the permitted source actually provides. Nothing is kept: files live in a temporary folder only while they're prepared and delivered.

> Personal use only. This project does not bypass DRM, logins, private accounts, geo-restrictions, bot checks or any other access control, and it never uses cookies, session tokens or credentials. When a platform withholds something, the app says so plainly.

---

## Features

| Area | What it does |
| --- | --- |
| Home | Paste any supported link. Local detection shows the platform instantly, then hands off to that platform's page, which asks the backend. |
| Instagram | Photo & Video downloader (post / reel / carousel, per-item download + Download All), Caption Copier, Highlights downloader with five distinct outcome states. |
| TikTok | Photo & Video downloader, Caption Copier (official oEmbed first). Prefers a watermark-free rendition **only if TikTok itself serves one**. |
| YouTube | Detects Short vs video, orientation, aspect ratio and duration. Lists **only** the qualities YouTube offers, requires an explicit pick, merges separate audio/video by stream copy. |
| Progress | Real server-side bytes and percentages, an honest indeterminate bar when size is unknown, then a real delivery counter until the file has fully streamed. |
| Privacy | No database, no accounts, no history. Temp files deleted on success, failure, cancel, TTL and restart. |
| UI | Dark by default, plus light and system themes. Bottom nav on phones, reduced-motion aware, keyboard and screen-reader friendly. |

## Architecture

```
Browser (Next.js, same-origin /api/*)
   │  rewrite
   ▼
FastAPI ── GuardMiddleware (request id, security headers, rate limit, body limit)
   │
   ├─ security/url_validation   strict host allowlist + canonical URL rebuild
   ├─ services/<platform>       PlatformService → ordered RetrievalProviders
   │     instagram: InstagramGraphProvider (official, own account) → InstagramEngineProvider
   │     tiktok:    TikTokOEmbedProvider (captions) → TikTokEngineProvider
   │     youtube:   YouTubeService + quality builder
   ├─ security/tickets          HMAC-signed, expiring tickets (stateless)
   ├─ processors/executor       engine or SSRF-safe direct fetch → temp dir → ZIP (stored)
   ├─ processors/jobs           in-memory job state machine
   └─ cleanup/                  TempStore + periodic sweeper
   ▼
GET /api/downloads/{id}/file   streamed once, then the job folder is deleted
```

Key decisions:

- **Signed tickets instead of storage.** Analysis responses carry opaque tickets (HMAC-SHA256, 30 min expiry). The server only downloads what it analyzed itself, so clients can never make it fetch arbitrary URLs. There's no database.
- **Provider chain.** Each platform service tries providers in order. `ProviderSkip` means "not mine, try the next one". Final answers such as private, deleted or DRM stop the chain, so the app never shops around for a way in. A newly permitted retrieval method is one new provider class; the frontend doesn't change.
- **Native browser download.** When a job is ready the browser's own download manager fetches the file, which streams to disk with no copy in page memory. The server counts the bytes it actually sends, so the UI can show real delivery progress and then "Download Complete".

### Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/health` | Engine/provider availability |
| POST | `/api/{instagram,tiktok,youtube}/analyze` | Media analysis |
| POST | `/api/{instagram,tiktok,youtube}/caption` | Caption only |
| POST | `/api/instagram/highlight` | Highlight analysis |
| POST | `/api/downloads` | `{ticket, quality_id?}` → job |
| GET / DELETE | `/api/downloads/{id}` | Poll progress / cancel (deletes temp files) |
| GET | `/api/downloads/{id}/file` | One-time streamed file |
| GET | `/api/preview?t=` | Signed thumbnail proxy (images only, 8 MB cap) |

Errors always look like `{"error": {"code", "title", "message", "retryable", "request_id"}}`. Stack traces, paths and upstream messages are logged against the request id and never returned.

## Tech stack

- **Frontend:** Next.js 15 (App Router), React 19, TypeScript (strict), Tailwind CSS v4, shadcn/ui-style primitives (CVA + Radix Slot), Lucide, Motion, next-themes, Sonner
- **Backend:** Python 3.11+, FastAPI, Pydantic v2, httpx, yt-dlp (retrieval engine), ffmpeg (stream-copy merging)

## Project structure

```
backend/
  app/
    main.py            app factory, lifespan (startup purge + sweeper), handlers
    api/               middleware, routes (health, media, downloads), state
    core/              config (env), errors (codes + user copy), logging
    security/          url_validation, ssrf, tickets, rate_limit
    services/          base contract, yt-dlp client + error mapping, instagram/, tiktok/, youtube/
    processors/        jobs (state machine), executor, archive
    cleanup/           temp_store, sweeper
    schemas/           public API models
    utils/             filenames, SSRF-safe http
  tests/               pytest suite with fake engine (no network)
frontend/
  app/                 layout, pages (/, /instagram, /tiktok, /youtube), SEO routes, icons
  components/          ui, brand, layout, downloader, media, progress, errors, home
  hooks/               useAnalyze, useDownload, useCopy
  lib/                 api client, url detection, download state machine, format, errors, clipboard
  types/               API types mirrored from backend schemas
```

## Local development

Requirements: Node 20.9+, Python 3.11+, **ffmpeg** on PATH (needed to merge YouTube video+audio).

**Backend**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env               # set SECRET_KEY
uvicorn app.main:app --reload --port 8000
```

API docs (dev only): http://localhost:8000/api/docs

**Frontend**

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev                        # http://localhost:3000
```

Or run both with Docker: `cp backend/.env.example backend/.env && docker compose up --build`.

## Environment variables

Backend (`backend/.env`):

| Variable | Default | Notes |
| --- | --- | --- |
| `SECRET_KEY` | random per process | Signs tickets. Set it in production. |
| `CORS_ORIGINS` | `http://localhost:3000` | Only needed if the browser calls the API directly |
| `TRUST_PROXY_HEADERS` | `false` | Use `X-Forwarded-For` for rate limiting, only behind your own proxy |
| `TEMP_DIR` | `<system tmp>/mr-content-downloader` | Job folders are `mr-job-<uuid>` |
| `TEMP_TTL_SECONDS` | `900` | Hard lifetime of any temp file or job |
| `MAX_DOWNLOAD_MB` | `2048` | Per-file cap (engine and direct fetch) |
| `MAX_CONCURRENT_JOBS` / `MAX_BUNDLE_ITEMS` | `3` / `30` | |
| `RATE_LIMIT_*_PER_MINUTE` | `20` analyze, `10` download | Token bucket per client IP |
| `INSTAGRAM_GRAPH_ACCESS_TOKEN`, `INSTAGRAM_GRAPH_USER_ID` | empty | Optional official provider (see below) |

Frontend (`frontend/.env.local`): `BACKEND_URL` (server-side rewrite target), `NEXT_PUBLIC_SITE_URL`, optional `NEXT_PUBLIC_API_BASE`.

Real `.env` files are ignored by git. Only the `.env.example` files are committed.

## Testing

```bash
cd backend && pytest          # URL validation, SSRF, tickets, rate limiting, quality lists,
                              # error mapping, services, executor, cleanup, HTTP API
cd frontend && npm test       # URL detection, download state machine, quality selection,
                              # error parsing, highlight states, clipboard logic
npm run typecheck && npm run lint
```

Platform access is never exercised in tests: a fake engine and fake providers stand in for the network.

## Privacy & storage

- No database, no accounts, no media library, no download history, and captions are never stored.
- Temp cleanup is layered on purpose: on success (after the file streams), on failure, on cancel (including leaving the page mid-job), on a periodic TTL sweep, at startup (abandoned `mr-job-*` folders) and at shutdown.
- Delivered files are one-time. A second request gets a 404.
- Logs contain request ids and error codes. Media URLs from the engine are kept out of the logs.

## Platform limitations (read this)

This project only uses logged-out public extraction plus official APIs. So:

- **Instagram photos:** the public extractor only exposes **videos**. Photo posts and image carousel items work through the **official Instagram API** (`INSTAGRAM_GRAPH_*`), and only for media on the account that owns the token. Otherwise you get a clear "not supported by the current retrieval method" message.
- **Instagram Highlights:** always attempted. Instagram currently serves Highlights only to signed-in viewers, and the official API has no Highlights endpoint, so many will show *Not supported by the current retrieval method*. The UI tells apart *retrieved*, *temporarily unavailable*, *unsupported*, *private/restricted*, *invalid URL* and *removed*. When a permitted provider appears, add it to `services/instagram/providers.py`.
- **TikTok:** videos work. Photo posts are not exposed as images by the engine, and the app explains this instead of faking it. Watermark status is shown only when the source labels it. "Watermark-free" is never claimed unless verified, and watermarks are never removed.
- **YouTube:** some videos require sign-in (age or members) or trigger bot checks. These are reported (`login_required`, `upstream_blocked`) and never worked around. Live streams are rejected.
- **Quality:** "Highest available quality" means the best rendition the permitted source offers. Nothing is upscaled, and nothing is re-encoded unless a container remux is needed.
- Platforms change often. Keep `yt-dlp` updated (`pip install -U yt-dlp`).

## Deployment considerations

- Put both services behind HTTPS. In production, route `/api/*` from your reverse proxy (Caddy/Nginx) **straight to FastAPI** so large files don't stream through Node, and set `proxy_buffering off` for `/api/downloads/*/file`.
- Run a single API worker. Jobs and rate limits live in process memory by design. For several workers you'd need a shared store, which this project deliberately avoids.
- Mount the temp dir on tmpfs or a small dedicated volume (the compose file uses tmpfs).
- Set a strong `SECRET_KEY`, `APP_ENV=production` (disables API docs, enables HSTS) and `TRUST_PROXY_HEADERS=true` only behind your own proxy.

## Legal & usage

Use this only for content you own or have permission to download, and follow Instagram's, TikTok's and YouTube's terms and applicable law (including copyright). The software is provided as-is for personal use. It is not affiliated with Meta, ByteDance or Google, and platform glyphs in the UI are simplified icons, not official logos.
