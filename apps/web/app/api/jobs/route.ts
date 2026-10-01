import { NextRequest, NextResponse } from "next/server";
import { getSupabase } from "@/lib/supabase";

export async function GET(request: NextRequest) {
  const url = new URL(request.url);
  const type = url.searchParams.get("type");
  const q = url.searchParams.get("q")?.trim();
  const location = url.searchParams.get("location")?.trim();
  const fresh = url.searchParams.get("fresh") === "1";
  const maxExpRaw = url.searchParams.get("max_exp");
  const maxExp = maxExpRaw ? Number(maxExpRaw) : null;
  const supabase = getSupabase();

  let query = supabase
    .from("jobs")
    .select("*")
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

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  return NextResponse.json({ jobs: data ?? [] });
}
