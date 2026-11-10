"""MCP server: unofficial read-only access to armut.com local services."""
from __future__ import annotations

import json
from datetime import datetime, timezone
import sys

from mcp.server.fastmcp import FastMCP

from . import http as _http
from . import services as _S

mcp = FastMCP("armut-mcp")

INSTRUCTIONS = """\
Unofficial read-only MCP server for armut.com, Türkiye's local-services \
marketplace (cleaning, moving, repairs, lessons, and 6,000+ more \
services). Data comes from armut.com's public server-rendered pages: \
service pages carry schema.org Product + ItemList (pros) + FAQPage \
JSON-LD, price-guide pages carry 12 months of price averages and real \
quote examples, the homepage carries trending/popular services, and the \
public price sitemap is the full 6,759-service catalogue. Service slugs \
look like "ev-temizligi", "evden-eve-nakliyat", "boyaci-boya-badana-ustasi"; \
city slugs like "istanbul", "ankara", "izmir" (use armut_search_services \
to find valid slugs; Turkish letters in a query are fine). Prices are in \
Turkish Lira (TRY) unless noted. Read-only, no login, no API key. Be \
polite: the server spaces requests ~0.8s apart. Built by Mohammad Abbasi \
(mohammad-abbasi-sh) — https://almanibama.ir · https://mabbasi.ir — Turkey MCP factory.\
"""


_SOURCE = "armut.com"
_DISCLAIMER = "Unofficial read-only data from armut.com; verify on the site before acting on it."


def _envelope() -> dict:
    return {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": _SOURCE,
        "disclaimer": _DISCLAIMER,
    }


def _ok(payload: dict) -> str:
    return json.dumps({**_envelope(), **payload}, ensure_ascii=False)


def _err(e: Exception) -> str:
    return _ok({"error": str(e)})


@mcp.tool()
def armut_search_services(query: str, limit: int = 10) -> str:
    """Search Armut's service catalogue (6,759 services) by keyword. \
query: Turkish or ASCII, e.g. "temizlik", "nakliyat", "boyaci" — matches \
service names/slugs; returns slug, service_id, price-guide URL and \
service-page URL for each match (use the slug with the other tools)."""
    try:
        xml = _http.fetch_price_sitemap()
        entries = _S.parse_price_sitemap(xml)
        rows = _S.search_services(entries, query, limit=limit)
    except _http.ArmutError as e:
        return _err(e)
    return _ok({"query": query, "count": len(rows), "services": rows})


@mcp.tool()
def armut_service_detail(service_slug: str) -> str:
    """Detail of one service: name, description, pro count, average \
rating and review count, service_id (needed for the price guide). \
service_slug: e.g. "ev-temizligi" (find slugs with \
armut_search_services)."""
    try:
        html = _http.fetch_service(service_slug)
        d = _S.parse_service_detail(html)
    except _http.ArmutError as e:
        return _err(e)
    return _ok(d)


@mcp.tool()
def armut_list_pros(service_slug: str, city: str = "",
                    limit: int = 10) -> str:
    """Top professionals for a service, with name, city/district, member \
since, bio, rating and review count, profile URL. service_slug: e.g. \
"ev-temizligi"; city: optional slug like "istanbul" to filter pros to \
that city; limit: 1..40 (the page lists up to 40)."""
    limit = max(1, min(int(limit), 40))
    try:
        html = _http.fetch_service(service_slug, city=city)
        pros = _S.parse_pros(html, limit=limit)
        detail = _S.parse_service_detail(html)
    except _http.ArmutError as e:
        return _err(e)
    return _ok({"service": detail.get("name", service_slug),
         "service_slug": service_slug, "city": city or "Türkiye geneli",
         "count": len(pros), "pros": pros})


@mcp.tool()
def armut_service_faq(service_slug: str) -> str:
    """Frequently asked questions for a service, with answers (from the \
service page's FAQ schema). service_slug: e.g. "ev-temizligi"."""
    try:
        html = _http.fetch_service(service_slug)
        faqs = _S.parse_faq(html)
    except _http.ArmutError as e:
        return _err(e)
    return _ok({"service_slug": service_slug, "count": len(faqs), "faq": faqs})


@mcp.tool()
def armut_price_guide(service_slug: str, city: str = "") -> str:
    """Price guide for a service: page-listed min/max price (TRY), 12 \
months of average/min/max prices with quote counts, total quotes and \
pro count, average rating, real example jobs with winning prices, and \
recent customer reviews. service_slug: e.g. "ev-temizligi"; city: \
optional slug like "adana" for that city's guide (default: all Türkiye)."""
    try:
        html = _http.fetch_service(service_slug)
        service_id = _S.parse_service_id(html)
        if not service_id:
            return _err(ValueError(
                f"could not find a service id for {service_slug!r}"))
        page = _http.fetch_price(service_slug, service_id, city=city)
        guide = _S.parse_price_page(_S.extract_next_data(page))
    except _http.ArmutError as e:
        return _err(e)
    return _ok(guide)


@mcp.tool()
def armut_trending_services() -> str:
    """What's popular on Armut right now: service groups (Temizlik, \
Tadilat, Nakliyat…), trending and popular services with pro counts, \
average ratings and verified review counts, and the most-searched \
city+service combos."""
    try:
        html = _http.fetch_home()
        data = _S.parse_homepage(_S.extract_next_data(html))
    except _http.ArmutError as e:
        return _err(e)
    return _ok(data)


@mcp.tool()
def armut_health() -> str:
    """Check whether armut.com is reachable right now.

    Returns status ok (HTTP 200), blocked (HTTP 403/429 — bot wall or
    rate limit) or error, plus the HTTP status and the probed URL.
    One polite request; it does not fetch any listings."""
    return _ok(_http.health_check())


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    sys.exit(main())
