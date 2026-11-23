// GET /api/subscribers  -> the daily robot reads sign-ups and unsubscribes here.
//
// Locked without any shared password: the robot sends the signed identity token that GitHub
// Actions gives every run (OIDC). We check GitHub's signature and that the token really comes
// from the jdmB3N/tenderpilot repository. Nobody else can produce such a token.
import { ensureTables, json } from "../../lib/db.js";

const ISSUER = "https://token.actions.githubusercontent.com";
const AUDIENCE = "tenderpilot-cloudflare";
const ALLOWED_REPO = "jdmB3N/tenderpilot";

const b64url = (s) => Uint8Array.from(atob(s.replace(/-/g, "+").replace(/_/g, "/").padEnd(Math.ceil(s.length / 4) * 4, "=")), (c) => c.charCodeAt(0));
const decodeJson = (s) => JSON.parse(new TextDecoder().decode(b64url(s)));

async function verifyGitHubToken(token) {
  const parts = token.split(".");
  if (parts.length !== 3) return null;
  const header = decodeJson(parts[0]);
  const claims = decodeJson(parts[1]);
  if (header.alg !== "RS256" || !header.kid) return null;
  const jwks = await (await fetch(`${ISSUER}/.well-known/jwks`, { cf: { cacheTtl: 3600 } })).json();
  const jwk = (jwks.keys || []).find((k) => k.kid === header.kid);
  if (!jwk) return null;
  const key = await crypto.subtle.importKey("jwk", jwk, { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" }, false, ["verify"]);
  const ok = await crypto.subtle.verify("RSASSA-PKCS1-v1_5", key, b64url(parts[2]),
    new TextEncoder().encode(`${parts[0]}.${parts[1]}`));
  if (!ok) return null;
  const now = Math.floor(Date.now() / 1000);
  const aud = Array.isArray(claims.aud) ? claims.aud : [claims.aud];
  if (claims.iss !== ISSUER || !aud.includes(AUDIENCE)) return null;
  if (!claims.exp || claims.exp < now || (claims.nbf && claims.nbf > now + 60)) return null;
  if (claims.repository !== ALLOWED_REPO) return null;
  return claims;
}

export async function onRequestGet({ request, env }) {
  const token = (request.headers.get("authorization") || "").replace(/^Bearer\s+/i, "");
  let claims = null;
  try { claims = token ? await verifyGitHubToken(token) : null; } catch { claims = null; }
  if (!claims) return json({ error: "Not allowed" }, 401);
  if (!env.DB) return json({ error: "Database not connected" }, 503);
  await ensureTables(env.DB);
  const subs = await env.DB.prepare(
    "SELECT company, email, does, countries, max_value, consent, created_at FROM subscribers ORDER BY created_at"
  ).all();
  const gone = await env.DB.prepare("SELECT email, created_at FROM unsubscribes").all();
  return json({ subscribers: subs.results || [], unsubscribes: gone.results || [] });
}
