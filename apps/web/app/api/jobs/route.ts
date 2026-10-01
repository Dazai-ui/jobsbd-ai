import { NextRequest, NextResponse } from "next/server";
import { getSupabase } from "@/lib/supabase";
import { sanitizeFilterTerm } from "@/lib/search";

export async function GET(request: NextRequest) {
  const url = new URL(request.url);
  const type = url.searchParams.get("type");
  const q = sanitizeFilterTerm(url.searchParams.get("q"));
  const location = sanitizeFilterTerm(url.searchParams.get("location"));
  const fresh = url.searchParams.get("fresh") === "1";
  const maxExpRaw = url.searchParams.get("max_exp");
  const maxExp = maxExpRaw ? Number(maxExpRaw) : null;
  const supabase = getSupabase();

  let query = supabase
    .from("jobs")
    .select("id,title,organization_name,department,location,employment_type,skills,job_category,academic_role,experience_min,experience_max,freshers_allowed,is_ai_ml,is_academic,relevance_score,posted_at,deadline,source_name,source_url,source_job_id,source_priority,status,first_seen_at,last_seen_at,created_at,updated_at")
    .eq("status", "active")
    .order("first_seen_at", { ascending: false })
    .limit(100);

  if (type === "ai") query = query.eq("is_ai_ml", true);
  if (type === "academic") query = query.eq("is_academic", true);

  if (q) {
    query = query.or(
      `title.ilike.%${q}%,organization_name.ilike.%${q}%,department.ilike.%${q}%,job_category.ilike.%${q}%`
    );
  }

  if (location) {
    query = query.ilike("location", `%${location}%`);
  }

  if (fresh) query = query.eq("freshers_allowed", true);

  if (maxExp != null && Number.isFinite(maxExp)) {
    query = query.or(
      `experience_max.lte.${maxExp},freshers_allowed.eq.true`
    );
  }

  const { data, error } = await query;

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  return NextResponse.json({ jobs: data ?? [] });
}
