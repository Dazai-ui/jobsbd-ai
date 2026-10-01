import { createClient } from "npm:@supabase/supabase-js@2.95.0";
import { createRemoteJWKSet, jwtVerify } from "npm:jose@6.1.0";

const EXPECTED_AUDIENCE = "jobsbd-ai-ingest";
const EXPECTED_REPOSITORY = "Dazai-ui/jobsbd-ai";
const EXPECTED_REPOSITORY_ID = "1399695814";
const EXPECTED_REF = "refs/heads/main";
const EXPECTED_WORKFLOW_REF =
  "Dazai-ui/jobsbd-ai/.github/workflows/crawl.yml@refs/heads/main";

const GITHUB_ISSUER = "https://token.actions.githubusercontent.com";
const GITHUB_JWKS = createRemoteJWKSet(
  new URL("https://token.actions.githubusercontent.com/.well-known/jwks"),
);

const JOB_FIELDS = new Set([
  "fingerprint",
  "title",
  "organization_name",
  "organization_id",
  "department",
  "location",
  "employment_type",
  "description",
  "requirements",
  "skills",
  "job_category",
  "academic_role",
  "experience_min",
  "experience_max",
  "freshers_allowed",
  "is_ai_ml",
  "is_academic",
  "relevance_score",
  "posted_at",
  "deadline",
  "source_id",
  "source_name",
  "source_url",
  "source_job_id",
  "source_priority",
  "raw_payload",
]);

function json(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json; charset=utf-8" },
  });
}

function getServiceKey() {
  const modernRaw = Deno.env.get("SUPABASE_SECRET_KEYS");
  if (modernRaw) {
    try {
      const parsed = JSON.parse(modernRaw);
      if (typeof parsed?.default === "string" && parsed.default) {
        return parsed.default;
      }
    } catch {
      // Fall back to the legacy injected service-role key below.
    }
  }

  const legacy = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if (!legacy) throw new Error("Supabase server secret is unavailable");
  return legacy;
}

function pickJobFields(job: Record<string, unknown>) {
  const clean: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(job)) {
    if (JOB_FIELDS.has(key)) clean[key] = value;
  }
  return clean;
}

async function verifyGitHubOidc(req: Request) {
  const auth = req.headers.get("authorization") ?? "";
  if (!auth.startsWith("Bearer ")) {
    throw new Error("Missing bearer token");
  }

  const token = auth.slice("Bearer ".length);
  const { payload } = await jwtVerify(token, GITHUB_JWKS, {
    issuer: GITHUB_ISSUER,
    audience: EXPECTED_AUDIENCE,
  });

  if (
    String(payload.repository ?? "").toLowerCase() !==
      EXPECTED_REPOSITORY.toLowerCase()
  ) {
    throw new Error("Repository claim rejected");
  }

  if (String(payload.repository_id ?? "") !== EXPECTED_REPOSITORY_ID) {
    throw new Error("Repository ID claim rejected");
  }

  if (payload.ref !== EXPECTED_REF) {
    throw new Error("Git ref rejected");
  }

  if (
    String(payload.workflow_ref ?? "").toLowerCase() !==
      EXPECTED_WORKFLOW_REF.toLowerCase()
  ) {
    throw new Error("Workflow claim rejected");
  }

  return payload;
}

const supabase = createClient(
  Deno.env.get("SUPABASE_URL") ?? "",
  getServiceKey(),
  { auth: { persistSession: false, autoRefreshToken: false } },
);

async function upsertJob(rawJob: Record<string, unknown>) {
  const job = pickJobFields(rawJob);

  for (const required of [
    "fingerprint",
    "title",
    "organization_name",
    "source_name",
    "source_url",
  ]) {
    if (!job[required]) throw new Error(`Missing job field: ${required}`);
  }

  const now = new Date().toISOString();
  const incomingPriority = Number(job.source_priority ?? 50);
  job.source_priority = incomingPriority;
  job.last_seen_at = now;

  const { data: existing, error: lookupError } = await supabase
    .from("jobs")
    .select("id,source_priority")
    .eq("fingerprint", job.fingerprint)
    .maybeSingle();

  if (lookupError) throw lookupError;

  let jobId: string;

  if (existing) {
    jobId = existing.id;
    const existingPriority = Number(existing.source_priority ?? 50);

    if (incomingPriority <= existingPriority) {
      const { error } = await supabase
        .from("jobs")
        .update({ ...job, updated_at: now })
        .eq("id", jobId);
      if (error) throw error;
    } else {
      const { error } = await supabase
        .from("jobs")
        .update({ last_seen_at: now })
        .eq("id", jobId);
      if (error) throw error;
    }
  } else {
    const { data, error } = await supabase
      .from("jobs")
      .insert(job)
      .select("id")
      .single();

    if (error) throw error;
    jobId = data.id;
  }

  const { error: sourceError } = await supabase
    .from("job_sources")
    .upsert(
      {
        job_id: jobId,
        source_name: job.source_name,
        source_url: job.source_url,
        source_job_id: job.source_job_id ?? null,
        source_priority: incomingPriority,
        last_seen_at: now,
      },
      { onConflict: "job_id,source_url" },
    );

  if (sourceError) throw sourceError;
  return jobId;
}

async function recordSourceRun(body: Record<string, unknown>) {
  const row = {
    source_name: String(body.source_name ?? ""),
    status: String(body.status ?? ""),
    discovered_count: Number(body.discovered_count ?? 0),
    accepted_count: Number(body.accepted_count ?? 0),
    error_message: body.error_message
      ? String(body.error_message).slice(0, 2000)
      : null,
  };

  if (!row.source_name) throw new Error("Missing source_name");
  if (!["success", "failed"].includes(row.status)) {
    throw new Error("Invalid source-run status");
  }

  const { error } = await supabase.from("source_runs").insert(row);
  if (error) throw error;
}

async function expirePastDeadlines() {
  const now = new Date().toISOString();
  const { data, error } = await supabase
    .from("jobs")
    .update({ status: "expired", updated_at: now })
    .eq("status", "active")
    .lt("deadline", now)
    .select("id");

  if (error) throw error;
  return data?.length ?? 0;
}

Deno.serve(async (req: Request) => {
  if (req.method !== "POST") {
    return json({ error: "Method not allowed" }, 405);
  }

  try {
    const claims = await verifyGitHubOidc(req);
    const body = await req.json();
    const action = String(body?.action ?? "");

    if (action === "health") {
      return json({
        ok: true,
        repository: claims.repository,
        ref: claims.ref,
      });
    }

    if (action === "upsert_job") {
      const id = await upsertJob(body.job ?? {});
      return json({ ok: true, id });
    }

    if (action === "record_source_run") {
      await recordSourceRun(body);
      return json({ ok: true });
    }

    if (action === "expire_past_deadlines") {
      const expired = await expirePastDeadlines();
      return json({ ok: true, expired });
    }

    return json({ error: "Unknown action" }, 400);
  } catch (error) {
    console.error(error);
    return json(
      { error: error instanceof Error ? error.message : "Unauthorized" },
      401,
    );
  }
});
