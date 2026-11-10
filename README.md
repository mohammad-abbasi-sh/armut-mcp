# armut-mcp 🇹🇷

mcp-name: io.github.mohammad-abbasi-sh/armut-mcp

Unofficial **read-only** MCP server for **armut.com**, Türkiye's local-services marketplace — search 6,759 services (cleaning, moving, repairs, lessons and more), browse top professionals with ratings and reviews, read service FAQs, and get price guides with 12 months of average prices and real quote examples.

> Built by Mohammad Abbasi as part of the "Turkey MCP factory" (Sepehr-style pipeline). Not affiliated with armut.com.

## For AI agents

Add to your MCP client config (stdio):

```json
{
  "mcpServers": {
    "armut": {
      "command": "uvx",
      "args": ["armut-mcp==0.1.1"]
    }
  }
}
```

Or run locally: `python -m armut_mcp.server` (needs `mcp<2`, `curl-cffi`).

## Tools

| Tool | Description |
|------|-------------|
| `armut_search_services` | Search the 6,759-service catalogue by keyword — `query` ("temizlik", "nakliyat", "boyaci"), Turkish letters fine; returns slug, service_id, price-guide and service-page URLs |
| `armut_service_detail` | Detail of one service (slug e.g. "ev-temizligi"): name, description, pro count, average rating, review count, service_id |
| `armut_list_pros` | Top professionals for a service: name, city/district, member since, bio, rating, review count, profile URL; `city` ("istanbul") filters to that city; `limit` 1..40 |
| `armut_service_faq` | Frequently asked questions for a service, with answers |
| `armut_price_guide` | Price guide for a service: page-listed min/max price (TRY), 12 months of average/min/max prices with quote counts, total quotes, pro count, rating, real example jobs with winning prices, recent reviews; `city` ("adana") for that city's guide |
| `armut_trending_services` | What's popular right now: service groups, trending/popular services with pro counts and ratings, most-searched city+service combos |

Example output (`armut_search_services` / "temizlik"):

```json
{"query": "temizlik", "count": 10, "services": [
  {"slug": "ev-temizligi", "name": "Ev Temizligi", "service_id": 191,
   "price_url": "https://armut.com/fiyatlari/ev-temizligi_191",
   "service_url": "https://armut.com/ev-temizligi"}, …]}
```

Example output (`armut_service_detail` / "ev-temizligi"):

```json
{"name": "Ev Temizliği", "service_id": 191, "pro_count": 10141,
 "rating_average": 4.6, "review_count": 415591,
 "description": "Güvenilir Ev Temizliği hizmeti al, zaman kazan, garantide ol. …",
 "url": "https://armut.com/ev-temizligi"}
```

Example output (`armut_list_pros` / "ev-temizligi", istanbul, 1):

```json
{"service": "Ev Temizliği", "city": "istanbul", "count": 1, "pros": [
  {"name": "Nermin K.", "location": "Şişli, İstanbul", "since": "…",
   "bio": "…", "rating": 4.1, "review_count": 162,
   "profile_url": "https://armut.com/hizmetveren/…"}]}
```

Example output (`armut_price_guide` / "ev-temizligi", adana):

```json
{"service": "Ev Temizliği", "service_id": 191, "city": "Adana",
 "currency": "TRY", "min_price_try": 479, "max_price_try": 1024,
 "quote_count": 790, "pro_count": 433, "rating_average": 4.6,
 "monthly_average_try": [
  {"month": "2025-11", "avg_try": 2756.39, "min_try": 1763,
   "max_try": 3806, "quotes": 88}, …]}
```

Notes:
- Data comes from armut.com's public server-rendered pages (schema.org Product/ItemList/FAQPage JSON-LD on service pages, `__NEXT_DATA__` on the homepage and price-guide pages, the public price sitemap) — no key, no login, read-only.
- Turkish `-lik` nouns surface as `-ligi` in slugs ("temizlik" → "ev-temizligi"); the search handles that, so a plain "temizlik" query finds "ev-temizligi".
- The page-listed min/max price and the 12 monthly averages come from different page fields; the monthly averages (with quote counts) are the more reliable price signal.
- Requests are spaced ~0.8s apart to stay polite.
- Environments behind an MITM proxy: set `SSL_CERT_FILE` to a CA bundle that trusts the proxy.

## Development

```bash
python3 -m venv .venv && .venv/bin/pip install "mcp<2" curl-cffi pytest
.venv/bin/pip install -e .
.venv/bin/python -m pytest tests/ -q
```

- `tests/test_services.py` — offline, parses real captured fixtures (29 tests)
- `tests/test_live.py` — 8 cautious live requests against armut.com (needs `SSL_CERT_FILE` behind the lab proxy)

## License

MIT

---

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
