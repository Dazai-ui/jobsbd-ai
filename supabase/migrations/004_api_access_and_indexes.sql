-- Public browser access: read-only job discovery.
grant select on table public.jobs to anon, authenticated;
grant select on table public.organizations to anon, authenticated;

-- Internal crawler/ops tables are not part of the public Data API surface.
revoke all on table public.sources from anon, authenticated;
revoke all on table public.job_sources from anon, authenticated;
revoke all on table public.source_runs from anon, authenticated;

-- Browser clients must never modify primary data directly.
revoke insert, update, delete, truncate, references, trigger
  on table public.jobs from anon, authenticated;
revoke insert, update, delete, truncate, references, trigger
  on table public.organizations from anon, authenticated;

-- Service-role crawler needs full table access; RLS is bypassed by service role.
grant select, insert, update, delete
  on table public.jobs, public.organizations, public.sources,
           public.job_sources, public.source_runs
  to service_role;

-- Cover foreign keys flagged by the database advisor.
create index if not exists sources_organization_id_idx
  on public.sources(organization_id);

create index if not exists jobs_organization_id_idx
  on public.jobs(organization_id);

create index if not exists jobs_source_id_idx
  on public.jobs(source_id);
