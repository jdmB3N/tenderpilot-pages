// GET /api/subscribers  -> the daily robot reads sign-ups and unsubscribes here.
// Locked: requires "Authorization: Bearer <ROBOT_SECRET>" (an encrypted variable in the Pages project).
import { ensureTables, json } from "../../lib/db.js";

function sameSecret(a, b) {
  if (!a || !b || a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

export async function onRequestGet({ request, env }) {
  const given = (request.headers.get("authorization") || "").replace(/^Bearer\s+/i, "");
  if (!env.ROBOT_SECRET || !sameSecret(given, env.ROBOT_SECRET)) return json({ error: "Not allowed" }, 401);
  if (!env.DB) return json({ error: "Database not connected" }, 503);
  await ensureTables(env.DB);
  const subs = await env.DB.prepare(
    "SELECT company, email, does, countries, max_value, consent, created_at FROM subscribers ORDER BY created_at"
  ).all();
  const gone = await env.DB.prepare("SELECT email, created_at FROM unsubscribes").all();
  return json({ subscribers: subs.results || [], unsubscribes: gone.results || [] });
}
