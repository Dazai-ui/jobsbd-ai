create extension if not exists pgcrypto;

create table if not exists organizations (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  org_type text not null check (org_type in ('company','university','portal','other')),
  website_url text,
  career_url text,
  active boolean not null default true,
  created_at timestamptz not null default now(),
  unique(name)
);

create table if not exists sources (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid references organizations(id) on delete set null,
  name text not null,
  source_type text not null check (source_type in ('official','portal','discovery')),
  base_url text,
  adapter text not null,
  config jsonb not null default '{}'::jsonb,
  enabled boolean not null default true,
  poll_minutes integer not null default 60,
  last_fetched_at timestamptz,
  created_at timestamptz not null default now(),
  unique(name)
);

create table if not exists jobs (
  id uuid primary key default gen_random_uuid(),
  fingerprint text not null unique,

  title text not null,
  organization_name text not null,
  organization_id uuid references organizations(id) on delete set null,

  department text,
  location text,
  employment_type text,

  description text,
  requirements text,
  skills text[] not null default '{}',

  job_category text,
  academic_role text,

  experience_min numeric,
  experience_max numeric,
  freshers_allowed boolean not null default false,

  is_ai_ml boolean not null default false,
  is_academic boolean not null default false,
  relevance_score numeric not null default 0,

  posted_at timestamptz,
  deadline timestamptz,

  source_id uuid references sources(id) on delete set null,
  source_name text not null,
  source_url text not null,
  source_job_id text,

  raw_payload jsonb not null default '{}'::jsonb,

  status text not null default 'active'
    check (status in ('active','expired','removed')),

  first_seen_at timestamptz not null default now(),
  last_seen_at timestamptz not null default now(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists jobs_status_idx on jobs(status);
create index if not exists jobs_deadline_idx on jobs(deadline);
create index if not exists jobs_ai_idx on jobs(is_ai_ml, status);
create index if not exists jobs_academic_idx on jobs(is_academic, status);
create index if not exists jobs_exp_idx on jobs(experience_max);
create index if not exists jobs_posted_idx on jobs(posted_at desc);
create index if not exists jobs_title_lower_idx on jobs(lower(title));
create index if not exists jobs_org_lower_idx on jobs(lower(organization_name));

alter table organizations enable row level security;
alter table sources enable row level security;
alter table jobs enable row level security;

drop policy if exists "public can read active jobs" on jobs;
create policy "public can read active jobs"
on jobs for select
using (status = 'active');

drop policy if exists "public can read organizations" on organizations;
create policy "public can read organizations"
on organizations for select
using (active = true);

-- No browser INSERT/UPDATE policies are created.
-- The crawler writes using the Supabase service-role key.
