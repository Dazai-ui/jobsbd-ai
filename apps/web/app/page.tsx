import Link from "next/link";
import { getSupabase } from "@/lib/supabase";
import type { Job } from "@/types/job";

export const revalidate = 300;

type SearchParams = Promise<{
  type?: string;
  q?: string;
  max_exp?: string;
  fresh?: string;
  location?: string;
}>;

function expLabel(job: Job) {
  if (job.freshers_allowed) return "Freshers allowed";
  if (job.experience_min != null && job.experience_max != null) {
    return `${job.experience_min}-${job.experience_max} yrs`;
  }
  if (job.experience_min != null) return `${job.experience_min}+ yrs`;
  if (job.experience_max != null) return `≤ ${job.experience_max} yrs`;
  return "Experience not specified";
}

function formatDate(value: string | null) {
  if (!value) return null;
  return new Intl.DateTimeFormat("en-BD", {
    day: "numeric",
    month: "short",
    year: "numeric"
  }).format(new Date(value));
}

export default async function Home({
  searchParams
}: {
  searchParams: SearchParams;
}) {
  const params = await searchParams;
  const type = params.type ?? "all";
  const q = params.q?.trim() ?? "";
  const location = params.location?.trim() ?? "";
  const fresh = params.fresh === "1";
  const maxExp = params.max_exp ? Number(params.max_exp) : null;

  const supabase = getSupabase();

  let query = supabase
    .from("jobs")
    .select(
      "id,title,organization_name,department,location,employment_type,skills,job_category,academic_role,experience_min,experience_max,freshers_allowed,is_ai_ml,is_academic,relevance_score,posted_at,deadline,source_name,source_url,first_seen_at"
    )
    .eq("status", "active")
    .order("first_seen_at", { ascending: false })
    .limit(100);

  if (type === "ai") query = query.eq("is_ai_ml", true);
  if (type === "academic") query = query.eq("is_academic", true);

  if (q) {
    const safe = q.replaceAll(",", " ");
    query = query.or(
      `title.ilike.%${safe}%,organization_name.ilike.%${safe}%,department.ilike.%${safe}%,job_category.ilike.%${safe}%`
    );
  }

  if (location) {
    query = query.ilike("location", `%${location.replaceAll(",", " ")}%`);
  }

  if (fresh) query = query.eq("freshers_allowed", true);

  if (maxExp != null && Number.isFinite(maxExp)) {
    query = query.or(
      `experience_max.lte.${maxExp},freshers_allowed.eq.true`
    );
  }

  const { data, error } = await query;
  const jobs = (data ?? []) as Job[];

  const tabHref = (nextType: string) => {
    const query = new URLSearchParams();
    if (nextType !== "all") query.set("type", nextType);
    if (q) query.set("q", q);
    if (location) query.set("location", location);
    if (params.max_exp) query.set("max_exp", params.max_exp);
    if (fresh) query.set("fresh", "1");
    const suffix = query.toString();
    return suffix ? `/?${suffix}` : "/";
  };

  return (
    <main>
      <section className="hero">
        <div className="eyebrow">Bangladesh job tracker</div>
        <h1>JobsBD AI</h1>
        <p>
          Entry-level AI/ML opportunities and university Lecturer, Faculty,
          RA, TA, Adjunct and Contractual roles collected from official
          career pages and selected public job portals.
        </p>
      </section>

      <form className="filters" method="get">
        {type !== "all" && <input type="hidden" name="type" value={type} />}

        <label className="field fieldWide">
          <span>Search</span>
          <input
            name="q"
            defaultValue={q}
            placeholder="Machine learning, CSE lecturer, university..."
          />
        </label>

        <label className="field">
          <span>Location</span>
          <input
            name="location"
            defaultValue={location}
            placeholder="Dhaka, Chattogram..."
          />
        </label>

        <label className="field">
          <span>Max experience</span>
          <select name="max_exp" defaultValue={params.max_exp ?? ""}>
            <option value="">Any</option>
            <option value="0">Fresh / 0 years</option>
            <option value="1">Up to 1 year</option>
            <option value="2">Up to 2 years</option>
          </select>
        </label>

        <label className="check">
          <input
            type="checkbox"
            name="fresh"
            value="1"
            defaultChecked={fresh}
          />
          <span>Freshers explicitly allowed</span>
        </label>

        <button className="primaryButton" type="submit">Search jobs</button>
        <Link className="clearButton" href={type === "all" ? "/" : `/?type=${type}`}>
          Clear
        </Link>
      </form>

      <nav className="tabs" aria-label="Job type">
        <Link className={`tab ${type === "all" ? "active" : ""}`} href={tabHref("all")}>
          All
        </Link>
        <Link className={`tab ${type === "ai" ? "active" : ""}`} href={tabHref("ai")}>
          AI / ML
        </Link>
        <Link className={`tab ${type === "academic" ? "active" : ""}`} href={tabHref("academic")}>
          University
        </Link>
      </nav>

      <div className="resultsBar">
        <strong>{jobs.length}</strong> matching {jobs.length === 1 ? "job" : "jobs"}
      </div>

      {error ? (
        <div className="empty">Could not load jobs: {error.message}</div>
      ) : jobs.length === 0 ? (
        <div className="empty">
          No matching jobs yet. Try clearing a filter or wait for the next crawler run.
        </div>
      ) : (
        <section className="grid">
          {jobs.map((job) => {
            const deadline = formatDate(job.deadline);
            const posted = formatDate(job.posted_at);

            return (
              <article key={job.id} className="card">
                <div className="cardTop">
                  <div>
                    <Link className="jobTitle" href={`/jobs/${job.id}`}>
                      {job.title}
                    </Link>
                    <div className="muted">
                      {job.organization_name}
                      {job.location ? ` · ${job.location}` : ""}
                    </div>
                  </div>

                  {deadline && (
                    <div className="deadline">
                      <span>Deadline</span>
                      <strong>{deadline}</strong>
                    </div>
                  )}
                </div>

                <div className="meta">
                  {job.is_ai_ml && <span className="pill">AI / ML</span>}
                  {job.is_academic && (
                    <span className="pill">
                      {job.academic_role?.replaceAll("_", " ") ?? "Academic"}
                    </span>
                  )}
                  <span className="pill">{expLabel(job)}</span>
                  {job.department && <span className="pill">{job.department}</span>}
                  {job.employment_type && <span className="pill">{job.employment_type}</span>}
                </div>

                <div className="cardFooter">
                  <span className="sourceLine">
                    {job.source_name}{posted ? ` · Posted ${posted}` : ""}
                  </span>
                  <div className="cardActions">
                    <Link className="secondaryButton" href={`/jobs/${job.id}`}>
                      Details
                    </Link>
                    <a
                      className="primaryButton small"
                      href={job.source_url}
                      target="_blank"
                      rel="noreferrer"
                    >
                      Original circular ↗
                    </a>
                  </div>
                </div>
              </article>
            );
          })}
        </section>
      )}
    </main>
  );
}
