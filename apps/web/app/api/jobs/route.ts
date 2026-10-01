import { NextRequest, NextResponse } from "next/server";
import { getSupabase } from "@/lib/supabase";

export async function GET(request: NextRequest) {
  const url = new URL(request.url);
  const type = url.searchParams.get("type");
  const q = url.searchParams.get("q")?.trim();
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
    const escaped = q.replaceAll(",", " ");
    query = query.or(
      `title.ilike.%${escaped}%,organization_name.ilike.%${escaped}%,department.ilike.%${escaped}%`
    );
  }

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
