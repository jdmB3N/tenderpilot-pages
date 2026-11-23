// POST /api/signup  -> saves a free-trial sign-up in D1.
import { clean, ensureTables, json, readBody, validEmail } from "../../lib/db.js";

const ALLOWED_MAX = new Set([0, 50000, 200000, 500000, 2000000]);

export async function onRequestPost({ request, env }) {
  if (!env.DB) return json({ error: "Sign-ups are not connected yet. Please try again later." }, 503);
  let b;
  try { b = await readBody(request); } catch { return json({ error: "Couldn't read the form." }, 400); }
  if (clean(b.website, 200)) return json({ ok: true }); // honeypot: bots fill hidden fields

  const company = clean(b.company, 120);
  const email = clean(b.email, 160).toLowerCase();
  const does = clean(b.does, 800);
  const countries = clean(b.countries, 200);
  const max = Number(b.max_value ?? 0);
  const consent = b.consent === "yes" || b.consent === true || b.consent === "on";

  if (!company || !does || !countries) return json({ error: "Please fill in every field." }, 400);
  if (!validEmail(email)) return json({ error: "Please check your email address." }, 400);
  if (!consent) return json({ error: "Please tick the box so we can email you." }, 400);
  if (!ALLOWED_MAX.has(max)) return json({ error: "Please pick a contract size." }, 400);

  await ensureTables(env.DB);
  const recent = await env.DB.prepare(
    "SELECT COUNT(*) AS n FROM subscribers WHERE email = ? AND created_at > datetime('now', '-1 day')"
  ).bind(email).first();
  if (recent && recent.n >= 5) return json({ error: "You've already signed up today." }, 429);

  await env.DB.prepare(
    "INSERT INTO subscribers (company, email, does, countries, max_value, consent, created_at) VALUES (?, ?, ?, ?, ?, 1, ?)"
  ).bind(company, email, does, countries, max, new Date().toISOString()).run();
  return json({ ok: true });
}

export const onRequestGet = () => json({ error: "Use POST" }, 405);
