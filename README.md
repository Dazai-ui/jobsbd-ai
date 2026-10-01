# JobsBD AI

Zero-cost Bangladesh-focused job aggregator for:

- Entry-level AI/ML/Data/LLM/CV/NLP roles (freshers to about 2 years experience)
- University-level early-career academic roles: Lecturer, Assistant Lecturer, Faculty Member, Research Assistant (RA), Teaching Assistant (TA), Adjunct Lecturer, and Contractual Lecturer

## Architecture

- `apps/web` — Next.js frontend/API for Vercel
- `services/crawler` — Python crawlers, normalization, filtering, and classification
- `supabase/migrations` — PostgreSQL schema and RLS
- `.github/workflows` — scheduled crawler execution using GitHub Actions

## Cost target

V1 is designed for practically $0/month using Vercel, Supabase free tier, and GitHub Actions.

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

## Setup

1. Create a free Supabase project.
2. Run `supabase/migrations/001_init.sql` in Supabase SQL Editor.
3. Optionally run `supabase/seed.sql`.
4. Configure `apps/web/.env.local`.
5. Start the frontend:
   ```bash
   cd apps/web
   npm install
   npm run dev
   ```
6. Test the crawler without writing to Supabase:
   ```bash
   cd services/crawler
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   DRY_RUN=true python runner.py
   ```

## Source policy

Each source gets its own adapter. Prefer official APIs, RSS, JSON/JSON-LD, and official career pages. Add HTML scraping only after checking the source's permitted access method and rate limits.

The current `demo_source.py` proves the ingestion path end-to-end. Real Bangladesh source adapters are the next milestone.
