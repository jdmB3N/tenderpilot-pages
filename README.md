# TenderPilot website (Cloudflare Pages)

- `site/`: home page with the sign-up form, privacy and unsubscribe pages
- `functions/api/`: sign-up, unsubscribe, and the locked list the daily robot reads (Cloudflare D1 database, binding name DB; secret ROBOT_SECRET)
- `lib/db.js`: shared database helpers
- `build.py`: builds the whole site into `public/`, including "Cleaning tenders in Malta: 8 open now" pages under /tenders/ from TED (the EU's free tender database)
- `static/`: files copied as-is (Google verification)

Cloudflare Pages build settings: build command `python build.py`, output directory `public`. A daily GitHub workflow pushes a small commit so Cloudflare rebuilds the tender pages every morning.
