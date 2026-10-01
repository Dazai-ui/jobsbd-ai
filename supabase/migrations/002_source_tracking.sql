create table if not exists job_sources (
  id uuid primary key default gen_random_uuid(),
  job_id uuid not null references jobs(id) on delete cascade,
  source_name text not null,
  source_url text not null,
  source_job_id text,
  first_seen_at timestamptz not null default now(),
  last_seen_at timestamptz not null default now(),
  unique(job_id, source_url)
);

create index if not exists job_sources_job_idx on job_sources(job_id);

create table if not exists source_runs (
  id uuid primary key default gen_random_uuid(),
  source_name text not null,
  status text not null check (status in ('success','failed')),
  discovered_count integer not null default 0,
  accepted_count integer not null default 0,
  error_message text,
  created_at timestamptz not null default now()
);

create index if not exists source_runs_source_created_idx
  on source_runs(source_name, created_at desc);

alter table job_sources enable row level security;
alter table source_runs enable row level security;

-- These tables are operational metadata. Browser clients do not need direct
-- write access. The service-role crawler can read/write them.
