alter table jobs
  add column if not exists source_priority smallint not null default 50;

alter table job_sources
  add column if not exists source_priority smallint not null default 50;

create index if not exists jobs_source_priority_idx
  on jobs(source_priority);

create index if not exists job_sources_priority_idx
  on job_sources(job_id, source_priority);
