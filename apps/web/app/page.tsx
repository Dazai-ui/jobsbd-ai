import { getSupabase } from "@/lib/supabase";
import type { Job } from "@/types/job";

export const revalidate = 300;

type SearchParams = Promise<{ type?: string }>;

function expLabel(job: Job) {
  if (job.freshers_allowed) return "Freshers allowed";
  if (job.experience_min != null && job.experience_max != null) {
    return `${job.experience_min}-${job.experience_max} yrs`;
  }
  if (job.experience_min != null) return `${job.experience_min}+ yrs`;
  if (job.experience_max != null) return `≤ ${job.experience_max} yrs`;
  return null;
}

export default async function Home({
  searchParams
}: {
  searchParams: SearchParams;
}) {
  const params = await searchParams;
  const type = params.type ?? "all";
  const supabase = getSupabase();

  let query = supabase
    .from("jobs")
    .select(
      "id,title,organization_name,department,location,employment_type,skills,job_category,academic_role,experience_min,experience_max,freshers_allowed,is_ai_ml,is_academic,posted_at,deadline,source_name,source_url"
    )
    .eq("status", "active")
    .order("first_seen_at", { ascending: false })
    .limit(60);

  if (type === "ai") query = query.eq("is_ai_ml", true);
  if (type === "academic") query = query.eq("is_academic", true);

  const { data, error } = await query;
  const jobs = (data ?? []) as Job[];

  return (
    <main>
      <section className="hero">
        <h1>JobsBD AI</h1>
        <p>
          Live discovery for entry-level AI/ML jobs and university-level
          Lecturer, Assistant Lecturer, Faculty, RA, TA, Adjunct and
          Contractual Lecturer roles in Bangladesh.
        </p>
      </section>

      <nav className="tabs">
        <a className={`tab ${type === "all" ? "active" : ""}`} href="/">
          All
        </a>
        <a className={`tab ${type === "ai" ? "active" : ""}`} href="/?type=ai">
          AI / ML
        </a>
        <a className={`tab ${type === "academic" ? "active" : ""}`} href="/?type=academic">
          University
        </a>
      </nav>

      {error ? (
        <div className="empty">Could not load jobs: {error.message}</div>
      ) : jobs.length === 0 ? (
        <div className="empty">No jobs yet. Run the crawler once to seed the feed.</div>
      ) : (
        <section className="grid">
          {jobs.map((job) => {
            const exp = expLabel(job);
            return (
              <a
                key={job.id}
                className="card"
                href={job.source_url}
                target="_blank"
                rel="noreferrer"
              >
                <h2>{job.title}</h2>
                <div className="muted">
                  {job.organization_name}
                  {job.location ? ` · ${job.location}` : ""}
                </div>

                <div className="meta">
                  {job.is_ai_ml && <span className="pill">AI/ML</span>}
                  {job.is_academic && (
                    <span className="pill">
                      {job.academic_role?.replaceAll("_", " ") ?? "Academic"}
                    </span>
                  )}
                  {exp && <span className="pill">{exp}</span>}
                  {job.department && <span className="pill">{job.department}</span>}
                  <span className="pill">{job.source_name}</span>
                </div>
              </a>
            );
          })}
        </section>
      )}
    </main>
  );
}
