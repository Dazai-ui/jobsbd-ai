# JobsBD AI

Zero-cost Bangladesh-focused job aggregator for:

- Entry-level AI/ML/Data/LLM/CV/NLP roles (freshers to about 2 years experience)
- University-level early-career academic roles: Lecturer, Assistant Lecturer, Faculty Member, Research Assistant (RA), Teaching Assistant (TA), Adjunct Lecturer, Contractual Lecturer, and close entry-level variants

## Architecture

- `apps/web` — Next.js frontend/API for Vercel
- `services/crawler` — Python source adapters, normalization, filtering, classification, deadline handling, and deduplication
- `supabase/migrations` — PostgreSQL schema and RLS
- `.github/workflows` — hourly crawler execution using GitHub Actions

## Cost target

V1 is designed for practically $0/month using Vercel, Supabase free tier, and GitHub Actions.

## Real sources currently wired

### United International University (UIU)

Official career archive: `https://www.uiu.ac.bd/career/`

The crawler discovers individual UIU career detail pages, extracts title, office/department, location, deadline, requirements, and filters for our target academic/AI roles.

### Pathao

Official openings page: `https://careers.pathao.com/job-openings/`

The crawler follows Pathao's individual job pages and extracts the complete circular text, experience requirements, location, job type, and application deadline.

### BRAC University

`career.bracu.ac.bd` is JavaScript-rendered. We are not adding a brittle HTML scraper that would silently produce bad data. It will get a dedicated adapter after its underlying data endpoint is confirmed.

## Filtering rules

Industry roles are kept when they are AI/ML/Data-related and appear to be fresher/junior/entry-level, normally no more than 2 years of required experience.

University roles currently include Lecturer, Assistant Lecturer, Faculty Member, Research Assistant, Teaching Assistant, Adjunct Lecturer/Faculty, Contractual Lecturer/Faculty, Part-time Lecturer, and Visiting Lecturer/Faculty.

Senior Lecturer, Assistant Professor, Associate Professor, Professor, and Dean are deliberately excluded from the entry-level academic track.

Expired jobs are dropped automatically when a parsable application deadline is available.

## Source isolation

Every source runs independently. If one career website changes or temporarily fails, other sources can still update the database. `source_runs` records source health and accepted/discovered counts.

## Deduplication

The first-pass fingerprint is source-independent when a deadline is known, so the same organization/title/deadline discovered through multiple websites can map to one job record. `job_sources` retains individual source URLs.

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

If the secrets are not configured, the scheduled workflow runs in `DRY_RUN` mode instead of failing.

## Supabase setup

Run the migrations in order:

1. `supabase/migrations/001_init.sql`
2. `supabase/migrations/002_source_tracking.sql`

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

Each source gets its own adapter or explicit configuration. Prefer official APIs, RSS, JSON/JSON-LD, and official career pages. HTML extraction is used only on public pages and with low-frequency polling. Do not add bypasses for access controls, anti-bot systems, or restricted content.
