create table if not exists public.source_health (
  source_name text primary key,
  last_status text not null default 'unknown',
  last_strategy text,
  last_success_at timestamptz,
  last_failure_at timestamptz,
  consecutive_failures integer not null default 0,
  last_discovered_count integer not null default 0,
  last_accepted_count integer not null default 0,
  last_error text,
  updated_at timestamptz not null default now()
);

create table if not exists public.source_state (
  source_name text not null,
  url text not null,
  strategy text not null default 'html',
  etag text,
  last_modified text,
  content_hash text,
  last_http_status integer,
  last_checked_at timestamptz not null default now(),
  last_changed_at timestamptz,
  metadata jsonb not null default '{}'::jsonb,
  primary key (source_name, url, strategy)
);

create index if not exists source_state_checked_idx
  on public.source_state(source_name, last_checked_at desc);

alter table public.source_health enable row level security;
alter table public.source_state enable row level security;

revoke all on table public.source_health from anon, authenticated;
revoke all on table public.source_state from anon, authenticated;

grant select, insert, update, delete
  on table public.source_health, public.source_state
  to service_role;
