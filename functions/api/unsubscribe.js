// POST /api/unsubscribe  -> records an unsubscribe; the daily robot stops emailing that address.
import { clean, ensureTables, json, readBody, validEmail } from "../../lib/db.js";

export async function onRequestPost({ request, env }) {
  if (!env.DB) return json({ error: "Not connected yet." }, 503);
  let b;
  try { b = await readBody(request); } catch { return json({ error: "Couldn't read the form." }, 400); }
  const email = clean(b.email, 160).toLowerCase();
  if (!validEmail(email)) return json({ error: "Please check the email address." }, 400);
  await ensureTables(env.DB);
  await env.DB.prepare("INSERT INTO unsubscribes (email, created_at) VALUES (?, ?)")
    .bind(email, new Date().toISOString()).run();
  return json({ ok: true });
}
