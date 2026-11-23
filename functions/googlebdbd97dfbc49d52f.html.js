// Google Search Console ownership file, served exactly at this address (no pretty-URL redirect).
export const onRequestGet = () =>
  new Response("google-site-verification: googlebdbd97dfbc49d52f.html", {
    headers: { "content-type": "text/html; charset=utf-8" },
  });
