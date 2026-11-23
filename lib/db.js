// Shared helpers for the TenderPilot API (Cloudflare Pages Functions + D1).
// The database binding must be named DB (Pages project > Settings > Bindings > D1 database).

export async function ensureTables(db) {
  await db.batch([
    db.prepare(`CREATE TABLE IF NOT EXISTS subscribers (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      company TEXT NOT NULL, email TEXT NOT NULL, does TEXT NOT NULL,
      countries TEXT NOT NULL, max_value INTEGER NOT NULL DEFAULT 0,
      consent INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL)`),
    db.prepare(`CREATE TABLE IF NOT EXISTS unsubscribes (
      id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT NOT NULL, created_at TEXT NOT NULL)`),
  ]);
}

export function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" },
  });
}

export async function readBody(request) {
  const type = request.headers.get("content-type") || "";
  if (type.includes("application/json")) return await request.json();
  const form = await request.formData();
  return Object.fromEntries(form);
}

export const clean = (v, max) => String(v ?? "").replace(/\s+/g, " ").trim().slice(0, max);
export const validEmail = (e) => /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(e) && e.length <= 160;
