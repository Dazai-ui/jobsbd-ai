import Link from "next/link";
import { notFound } from "next/navigation";
import { getSupabase } from "@/lib/supabase";

export const dynamic = "force-dynamic";
export const revalidate = 0;

type Params = Promise<{ id: string }>;

function formatDate(value: string | null) {
  if (!value) return "Not specified";
  return new Intl.DateTimeFormat("en-BD", {
    day: "numeric",
    month: "long",
    year: "numeric"
  }).format(new Date(value));
}

function experienceLabel(job: {
  freshers_allowed: boolean;
  experience_min: number | null;
  experience_max: number | null;
}) {
  if (job.freshers_allowed) return "Freshers explicitly allowed";
  if (job.experience_min != null && job.experience_max != null) {
    return `${job.experience_min}–${job.experience_max} years`;
  }
  if (job.experience_min != null) return `${job.experience_min}+ years`;
  if (job.experience_max != null) return `Up to ${job.experience_max} years`;
  return "Not specified";
}

export default async function JobDetail({ params }: { params: Params }) {
  const { id } = await params;
  const supabase = getSupabase();

  const { data: job, error } = await supabase
    .from("jobs")
    .select(
      "id,title,organization_name,department,location,employment_type,skills,job_category,academic_role,experience_min,experience_max,freshers_allowed,is_ai_ml,is_academic,posted_at,deadline,source_name,source_url"
    )
    .eq("id", id)
    .eq("status", "active")
    .single();

  if (error || !job) notFound();

  return (
    <main>
      <Link className="detailBack" href="/">← Back to jobs</Link>

      <article className="detailCard">
        <div className="eyebrow">
          {job.is_academic ? "University opportunity" : "AI / tech opportunity"}
        </div>

        <h1>{job.title}</h1>
        <div className="muted">
          {job.organization_name}
          {job.location ? ` · ${job.location}` : ""}
        </div>

        <div className="meta">
          {job.is_ai_ml && <span className="pill">AI / ML</span>}
          {job.is_academic && (
            <span className="pill">
              {job.academic_role?.replaceAll("_", " ") ?? "Academic"}
            </span>
          )}
          {job.department && <span className="pill">{job.department}</span>}
          {job.job_category && <span className="pill">{job.job_category}</span>}
        </div>

        <section className="detailGrid">
          <div className="detailItem">
            <span>Experience</span>
            <strong>{experienceLabel(job)}</strong>
          </div>
          <div className="detailItem">
            <span>Employment</span>
            <strong>{job.employment_type ?? "Not specified"}</strong>
          </div>
          <div className="detailItem">
            <span>Posted</span>
            <strong>{formatDate(job.posted_at)}</strong>
          </div>
          <div className="detailItem">
            <span>Deadline</span>
            <strong>{formatDate(job.deadline)}</strong>
          </div>
          <div className="detailItem">
            <span>Source</span>
            <strong>{job.source_name}</strong>
          </div>
          <div className="detailItem">
            <span>Location</span>
            <strong>{job.location ?? "Not specified"}</strong>
          </div>
        </section>

        {job.skills?.length > 0 && (
          <>
            <h2>Detected skills</h2>
            <div className="meta">
              {job.skills.map((skill: string) => (
                <span className="pill" key={skill}>{skill}</span>
              ))}
            </div>
          </>
        )}

        <p className="notice">
          JobsBD AI extracts structured metadata for discovery. Always verify
          eligibility, requirements, application instructions and deadlines in
          the original employer or university circular before applying.
        </p>

        <div className="detailActions">
          <a
            className="primaryButton"
            href={job.source_url}
            target="_blank"
            rel="noreferrer"
          >
            View original circular ↗
          </a>
          <Link className="secondaryButton" href="/">
            Browse more jobs
          </Link>
        </div>
      </article>
    </main>
  );
}
