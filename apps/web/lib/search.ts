export function sanitizeFilterTerm(value: string | undefined | null) {
  if (!value) return "";

  return value
    .normalize("NFKC")
    .replace(/[^\p{L}\p{N}\s._+#&/\-]/gu, " ")
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, 80);
}
