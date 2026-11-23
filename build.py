"""TenderPilot public pages: "Cleaning tenders in Malta: 8 open now", for every EU country x trade.

Runs daily (GitHub Actions) and writes a static site to ./public for GitHub Pages.
No keys needed: tender data comes from TED, the EU's free public tender database.
Every page links to the sign-up page, so Google visitors become free-trial sign-ups.
"""
import html
import json
import time
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

import httpx

SIGNUP = "https://laughing-tender-pilot-flow.base44.app/#start"
BASE_URL = "https://tenderpilot-pages.example"  # replaced by the real address in the workflow (SITE_BASE)
OUT = Path(__file__).resolve().parent / "public"
TED = "https://api.ted.europa.eu/v3/notices/search"

TRADES = {  # slug: (name, plural customer word, CPV codes)
    "cleaning": ("Cleaning", "cleaning companies", ["90910000", "90911000", "90911200", "90919000"]),
    "construction": ("Construction", "builders and contractors", ["45000000", "45200000", "45400000", "45450000"]),
    "it-software": ("IT and software", "IT and software companies", ["72000000", "72200000", "72260000", "48000000"]),
    "websites-marketing": ("Websites and marketing", "web and marketing agencies", ["72413000", "79340000", "79341000", "79342000", "79416000"]),
    "security": ("Security", "security companies", ["79710000", "79713000", "79714000"]),
    "catering": ("Catering and food", "caterers", ["55300000", "55320000", "55520000", "55524000"]),
    "electrical": ("Electrical", "electricians", ["45310000", "45311000", "45315000", "31600000"]),
    "translation": ("Translation", "translators and language agencies", ["79530000", "79540000"]),
}
COUNTRIES = {"AUT": "Austria", "BEL": "Belgium", "BGR": "Bulgaria", "HRV": "Croatia", "CYP": "Cyprus",
             "CZE": "Czechia", "DNK": "Denmark", "EST": "Estonia", "FIN": "Finland", "FRA": "France",
             "DEU": "Germany", "GRC": "Greece", "HUN": "Hungary", "IRL": "Ireland", "ITA": "Italy",
             "LVA": "Latvia", "LTU": "Lithuania", "LUX": "Luxembourg", "MLT": "Malta", "NLD": "Netherlands",
             "POL": "Poland", "PRT": "Portugal", "ROU": "Romania", "SVK": "Slovakia", "SVN": "Slovenia",
             "ESP": "Spain", "SWE": "Sweden"}
FIELDS = ["publication-number", "notice-title", "buyer-name", "buyer-country",
          "deadline-receipt-tender-date-lot", "estimated-value-lot", "estimated-value-cur-lot"]


def pick(v):
    if isinstance(v, dict):
        for l in ("eng",):
            if v.get(l):
                return v[l][0] if isinstance(v[l], list) else v[l]
        for x in v.values():
            return x[0] if isinstance(x, list) else x
    if isinstance(v, list):
        return v[0] if v else ""
    return v or ""


def fetch_trade(cpv: list[str]) -> list[dict]:
    """Open tenders for one trade, all EU countries, published in the last 30 days."""
    since = (date.today() - timedelta(days=30)).strftime("%Y%m%d")
    today = date.today().isoformat()
    q = f"classification-cpv IN ({' '.join(cpv)}) AND publication-date >= {since} AND notice-type IN (cn-standard cn-social)"
    out, page = [], 1
    while page <= 16:  # up to 4,000 notices per trade
        try:
            r = httpx.post(TED, json={"query": q, "fields": FIELDS, "limit": 250, "page": page}, timeout=60)
            r.raise_for_status()
        except Exception as e:
            print("TED error:", str(e)[:120])
            break
        notices = r.json().get("notices", [])
        for n in notices:
            deadlines = sorted(d[:10] for d in (n.get("deadline-receipt-tender-date-lot") or []) if d[:10] >= today)
            if not deadlines:
                continue  # already closed
            vals = [float(v) for v in (n.get("estimated-value-lot") or []) if str(v).replace(".", "", 1).isdigit()]
            pub = n.get("publication-number", "")
            title = pick(n.get("notice-title"))
            out.append({"id": pub, "title": title.split(" – ", 2)[-1] if title.count(" – ") >= 2 else title,
                        "buyer": pick(n.get("buyer-name")), "country": pick(n.get("buyer-country")),
                        "deadline": deadlines[0], "value": sum(vals) if vals else None,
                        "cur": pick(n.get("estimated-value-cur-lot")) or "EUR",
                        "link": f"https://ted.europa.eu/en/notice/-/detail/{pub}"})
        if len(notices) < 250:
            break
        page += 1
        time.sleep(1)
    return out


CSS = """:root{--bg:#F6F3EC;--card:#FBFAF6;--ink:#121A2B;--soft:#4A5568;--line:#E2DCCD;--amber:#F2A93B;--eye:#9A6413}
@media (prefers-color-scheme:dark){:root{--bg:#0F1522;--card:#18213A;--ink:#F1EEE6;--soft:#B8C0D0;--line:#2C3756;--eye:#F2A93B}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:17px/1.55 Arial,sans-serif}
.w{max-width:860px;margin:0 auto;padding:0 16px}nav{padding:18px 0;font-weight:700;font-size:20px}nav a{color:inherit;text-decoration:none}nav span{color:var(--amber)}
h1{font-size:clamp(28px,5vw,40px);line-height:1.15;margin:12px 0}.eye{font-size:13px;letter-spacing:2px;text-transform:uppercase;color:var(--eye);font-weight:700}
.soft{color:var(--soft)}.t{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px;margin:12px 0}
.t h2{font-size:18px;margin:0 0 6px;line-height:1.3}.t p{margin:0;font-size:15px;color:var(--soft)}.t a{color:var(--eye)}
.cta{background:var(--ink);color:var(--bg);border-radius:18px;padding:24px;margin:28px 0}.cta a{display:inline-block;background:var(--amber);color:#121A2B;font-weight:700;padding:12px 22px;border-radius:99px;text-decoration:none;margin-top:10px}
.grid{display:flex;flex-wrap:wrap;gap:8px}.grid a{background:var(--card);border:1px solid var(--line);border-radius:99px;padding:6px 12px;color:var(--ink);text-decoration:none;font-size:14px}
footer{padding:28px 0 40px;font-size:13px;color:var(--soft)}"""


def page(title: str, desc: str, body: str, path: str) -> str:
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title><meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="{BASE_URL}/{path}"><style>{CSS}</style></head><body><div class="w">
<nav><a href="{BASE_URL}/">Tender<span>Pilot</span></a></nav>{body}
<footer>Updated {date.today():%d %B %Y}. Data from TED, the EU's official public tender database. Always read the official notice before you apply.</footer>
</div></body></html>"""


def money(t):
    return f"{t['cur']} {t['value']:,.0f}" if t.get("value") else "Value not stated"


def cta(trade_people: str, where: str) -> str:
    return (f'<div class="cta"><b style="font-size:20px">Get new {where} in your inbox every morning</b>'
            f'<p style="margin:6px 0 0;opacity:.85">TenderPilot reads every new public tender and emails {trade_people} only the ones that fit them, '
            f'scored by AI, with the deadline. Free for 14 days, no card.</p><a href="{SIGNUP}">Start free</a></div>')


def tender_card(t) -> str:
    return (f'<div class="t"><h2>{html.escape(t["title"])}</h2><p>{html.escape(t["buyer"])} · {COUNTRIES.get(t["country"], t["country"])}'
            f' · <b>Deadline {t["deadline"]}</b> · {money(t)} · <a href="{t["link"]}" rel="nofollow">Official notice</a></p></div>')


def build():
    OUT.mkdir(exist_ok=True)
    urls, index_links, totals = [], [], defaultdict(int)
    for slug, (name, people, cpv) in TRADES.items():
        tenders = fetch_trade(cpv)
        by_c = defaultdict(list)
        for t in tenders:
            if t["country"] in COUNTRIES:
                by_c[t["country"]].append(t)
        links = []
        for code, cname in COUNTRIES.items():
            items = sorted(by_c.get(code, []), key=lambda t: t["deadline"])
            path = f"{slug}-tenders-{cname.lower()}.html"
            n = len(items)
            title = f"{name} tenders in {cname}: {n} open now ({date.today():%B %Y})"
            desc = (f"{n} open public {name.lower()} tenders in {cname}, updated daily, with deadlines and values. "
                    f"Get matching tenders by email every morning.")
            intro = (f'<p class="eye">{name} · {cname}</p><h1>{html.escape(title)}</h1>'
                     f'<p class="soft">Government bodies in {cname} publish {name.lower()} contracts as public tenders. '
                     f'Here are the ones still open, soonest deadline first. This page updates every day.</p>')
            listing = "".join(tender_card(t) for t in items[:40]) or (
                f'<p class="soft">No open {name.lower()} tenders in {cname} were published on TED in the last 30 days. '
                f'New ones appear often. Get them by email the morning they are published.</p>')
            (OUT / path).write_text(page(title, desc, intro + cta(people, f"{name.lower()} tenders in {cname}") + listing, path), encoding="utf-8")
            urls.append(path)
            links.append(f'<a href="{path}">{cname} ({n})</a>')
            totals[slug] += n
        hub = f"{slug}-tenders.html"
        title = f"{name} tenders in Europe: {totals[slug]} open now"
        body = (f'<p class="eye">{name}</p><h1>{title}</h1><p class="soft">Open public {name.lower()} tenders by country, updated daily.</p>'
                f'<div class="grid">{"".join(links)}</div>' + cta(people, f"{name.lower()} tenders"))
        (OUT / hub).write_text(page(title, f"Open public {name.lower()} tenders in every EU country, updated daily.", body, hub), encoding="utf-8")
        urls.append(hub)
        index_links.append(f'<a href="{hub}">{name} ({totals[slug]})</a>')
        print(f"{name}: {len(tenders)} open tenders")
        time.sleep(1)
    body = ('<p class="eye">Public tenders, updated daily</p><h1>Find government contracts your business can win</h1>'
            '<p class="soft">Every open public tender in the EU, sorted by trade and country. Pick your trade:</p>'
            f'<div class="grid">{"".join(index_links)}</div>' + cta("small businesses", "matching tenders"))
    (OUT / "index.html").write_text(page("Public tenders by trade and country | TenderPilot",
                                         "Open government tenders in every EU country, by trade, updated daily.", body, ""), encoding="utf-8")
    urls.append("")
    sitemap = "".join(f"<url><loc>{BASE_URL}/{u}</loc><lastmod>{date.today()}</lastmod></url>" for u in urls)
    (OUT / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sitemap}</urlset>', encoding="utf-8")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {BASE_URL}/sitemap.xml\n", encoding="utf-8")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    print(f"{len(urls)} pages written")


if __name__ == "__main__":
    import os
    BASE_URL = os.getenv("SITE_BASE", BASE_URL).rstrip("/")
    build()
