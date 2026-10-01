insert into organizations (name, org_type, website_url, career_url)
values
  ('Demo AI Company', 'company', 'https://example.com', 'https://example.com/careers'),
  ('Demo University', 'university', 'https://example.edu', 'https://example.edu/careers')
on conflict (name) do nothing;

insert into sources (name, source_type, base_url, adapter, config, poll_minutes)
values
  ('Demo Source', 'official', 'https://example.com', 'demo_source', '{"mode":"demo"}', 60)
on conflict (name) do nothing;
