# JobsBD AI

Zero-cost Bangladesh-focused job aggregator for:

- Entry-level AI/ML/Data/LLM/CV/NLP roles (freshers to about 2 years experience)
- University-level early-career academic roles: Lecturer, Assistant Lecturer, Faculty Member, Research Assistant (RA), Teaching Assistant (TA), Adjunct Lecturer/Faculty, Contractual Lecturer/Faculty, Part-time Lecturer, and Visiting Lecturer/Faculty

## Architecture

- `apps/web` — Next.js frontend/API for Vercel
- `services/crawler` — Python source adapters, normalization, filtering, classification, deadline handling, and deduplication
- `supabase/migrations` — PostgreSQL schema and RLS
- `.github/workflows` — CI plus automatic 30-minute crawler execution using GitHub Actions

## Cost target

V1 is designed for practically $0/month using Vercel, Supabase free tier, and GitHub Actions.

## Official sources currently wired

### University / academic

- United International University (UIU) — HTML career detail pages
- North South University (NSU) — official recruitment portal
- University of Liberal Arts Bangladesh (ULAB) — row-level faculty tables
- American International University-Bangladesh (AIUB) — linked faculty PDF circulars
- East West University (EWU) — career archive + academic/RA PDF circulars
- University of Dhaka — official job portal and job-detail pages

### Company career pages

- Brain Station 23 — Easy.Jobs career board, AI/data title-prefiltered
- Enosis Solutions — official careers board, AI/data title-prefiltered
- Therap (BD) Ltd. — Trakstar Hire board, AI/data title-prefiltered
- Optimizely — Dhaka/global careers board, AI/data title-prefiltered
- DataSoft Systems Bangladesh — official career pages; expired postings are discarded
- Pathao
- Cefalo
- ShopUp

### Job portals

- Bdjobs — public IT/Telecommunication listings, AI/data title-prefiltered before detail fetching
- Job.com.bd — public IT/Computer listings, AI/data title-prefiltered before detail fetching

## Pending / special handling

BRAC University's career portal is JavaScript-rendered, so it is intentionally not scraped with a brittle HTML workaround. It should get a dedicated adapter only after its public data endpoint is confirmed.

More official university/company sources and job portals will be added incrementally. bKash currently routes its "current jobs" button to Facebook rather than a structured public vacancy feed, so it is not scraped as an official source yet. BJIT currently reports no vacancies. Skill.Jobs and bdRecruit are currently disabled because automated fetches return HTTP 403; the project will not bypass access controls.

## Filtering rules

Industry roles are kept when they are AI/ML/Data-related and appear to be fresher/junior/entry-level, normally no more than 2 years of required experience.

University roles include Lecturer, Assistant Lecturer, Faculty Member, Research Assistant, Teaching Assistant, Adjunct Lecturer/Faculty, Contractual Lecturer/Faculty, Part-time Lecturer, and Visiting Lecturer/Faculty.

Senior Lecturer, Assistant Professor, Associate Professor, Professor, and Dean are excluded from the entry-level academic track.

Expired jobs are dropped automatically when a parsable application deadline is available.

## Cost-control rules

- Career pages are polled automatically every 30 minutes.
- Expired PDF circulars are skipped before download when the archive exposes a deadline.
- No paid LLM/API is required for classification.
- No paid standalone load balancer is required for V1.
- One source failure does not abort the remaining source runs.

## Source isolation and health

Every source runs independently. If one career website changes or temporarily fails, other sources still update the database.

`source_runs` records:

- source name
- success/failure
- discovered jobs
- accepted jobs
- error message
- run timestamp

## Deduplication and source priority

The first-pass fingerprint is source-independent when a deadline is known, so the same organization/title/deadline found on multiple websites can map to one job.

`job_sources` preserves every discovered source URL. Primary-source precedence is:

1. Official employer/university pages — priority 10
2. Job portals — priority 30
3. Discovery sources — priority 50
4. Demo/test data — priority 90

A lower-quality portal source cannot replace an official application link already stored for the same job.

The crawler also marks previously stored jobs as `expired` after their application deadline passes.

## Environment variables

### Web / Vercel

```bash
NEXT_PUBLIC_SUPABASE_URL=https://hxywgajeikdvoxbiohfq.supabase.co
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=sb_publishable_054cvShsfQ89th_lgxn36Q_uSpEWTlf
```

### GitHub Actions / crawler

The crawler does **not** store a Supabase service-role secret in GitHub.

GitHub Actions requests a short-lived GitHub OIDC token and sends it to the
`github-ingest` Supabase Edge Function. The function only accepts tokens for
this repository, `main`, and `.github/workflows/crawl.yml`, then performs
database writes using Supabase server-side credentials.

This keeps the GitHub repository free of long-lived Supabase secrets.

## Supabase setup

Run the migrations in order:

1. `supabase/migrations/001_init.sql`
2. `supabase/migrations/002_source_tracking.sql`
3. `supabase/migrations/003_source_priority.sql`
4. `supabase/migrations/004_api_access_and_indexes.sql`

Optionally run `supabase/seed.sql`.

## Local crawler test

```bash
cd services/crawler
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
DRY_RUN=true python runner.py
```

## Source policy

Each source gets its own adapter or explicit configuration. Prefer official APIs, RSS, JSON/JSON-LD, and official career pages. HTML/PDF extraction is used only on public pages with low-frequency polling. Do not add bypasses for access controls, anti-bot systems, or restricted content.


## CI

- `crawl.yml` runs tests and automatically crawls/ingests jobs every 30 minutes using GitHub OIDC.
- `web-ci.yml` runs TypeScript checking and a production Next.js build for frontend changes.
- `keepalive.yml` creates one monthly heartbeat commit so GitHub does not disable scheduled workflows after 60 days of repository inactivity.
