# JobsBD AI

Zero-cost Bangladesh-focused job aggregator for:

- Entry-level AI/ML/Data/LLM/CV/NLP roles (freshers to about 2 years experience)
- University-level early-career academic roles: Lecturer, Assistant Lecturer, Faculty Member, Research Assistant (RA), Teaching Assistant (TA), Adjunct Lecturer/Faculty, Contractual Lecturer/Faculty, Part-time Lecturer, and Visiting Lecturer/Faculty

## Architecture

- `apps/web` — Next.js frontend/API for Vercel
- `services/crawler` — Python source adapters, normalization, filtering, classification, deadline handling, and deduplication
- `supabase/migrations` — PostgreSQL schema and RLS
- `.github/workflows` — push CI plus hourly crawler execution using GitHub Actions

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

- Pathao
- Cefalo
- ShopUp

### Job portals

- Skill.Jobs — title-prefiltered before detail fetching to keep crawler cost low

## Pending / special handling

BRAC University's career portal is JavaScript-rendered, so it is intentionally not scraped with a brittle HTML workaround. It should get a dedicated adapter only after its public data endpoint is confirmed.

More official university/company sources and job portals will be added incrementally. bdRecruit is currently not enabled because direct automated fetches are returning HTTP 403; the project will not bypass access controls.

## Filtering rules

Industry roles are kept when they are AI/ML/Data-related and appear to be fresher/junior/entry-level, normally no more than 2 years of required experience.

University roles include Lecturer, Assistant Lecturer, Faculty Member, Research Assistant, Teaching Assistant, Adjunct Lecturer/Faculty, Contractual Lecturer/Faculty, Part-time Lecturer, and Visiting Lecturer/Faculty.

Senior Lecturer, Assistant Professor, Associate Professor, Professor, and Dean are excluded from the entry-level academic track.

Expired jobs are dropped automatically when a parsable application deadline is available.

## Cost-control rules

- Career pages are polled at low frequency.
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
NEXT_PUBLIC_SUPABASE_URL=...
NEXT_PUBLIC_SUPABASE_ANON_KEY=...
```

### GitHub Actions / crawler

Create repository secrets:

```bash
SUPABASE_URL=...
SUPABASE_SERVICE_ROLE_KEY=...
```

Never expose the Supabase service-role key in browser code.

If the secrets are not configured, GitHub Actions runs the live crawler in `DRY_RUN` mode instead of failing.

## Supabase setup

Run the migrations in order:

1. `supabase/migrations/001_init.sql`
2. `supabase/migrations/002_source_tracking.sql`
3. `supabase/migrations/003_source_priority.sql`

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

- `crawl.yml` runs crawler tests and a live dry-run when Supabase secrets are absent.
- `web-ci.yml` runs TypeScript checking and a production Next.js build for frontend changes.
