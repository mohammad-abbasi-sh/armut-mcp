"""Domain logic: parse armut.com public pages into compact dicts (stdlib only).

Data sources (all embedded in the public HTML, no JS needed):
- Homepage: __NEXT_DATA__ JSON with service groups, trending / popular
  services (serviceId, name, slug, proCount, ratingAverage,
  verifiedReviewsCount) and most-searched city+service combos.
- Service pages (/{slug} and /{city}-{slug}): schema.org JSON-LD —
  Product (name, description, image, aggregateRating), ItemList of pros
  (name, profile URL, rating, review count) and FAQPage; a hidden
  <input id="serviceId">; server-rendered <app-pro-card> blocks with
  name, place ("Ev Temizliği · Altıeylül, Balıkesir"), since-date, bio.
- Price-guide pages (/fiyatlari/{slug}_{id} and /fiyatlari/{city}-{slug}_{id}_1):
  __NEXT_DATA__ pricePageData — min/max price, 12 monthly averages with
  quote counts, quote count, pro count, rating, example jobs with winning
  prices, consumer reviews, district price pages.
- Price sitemap (/sitemap/price-1.xml): the full service catalogue —
  6,759 /fiyatlari/{slug}_{id} URLs; the search index.
"""
from __future__ import annotations

import html as _html
import json
import re

_NEXT_DATA_RE = re.compile(
    r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
    re.S)
_LDJSON_RE = re.compile(
    r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', re.S)
_SERVICE_ID_RE = re.compile(
    r'<input id="serviceId" type="hidden" value="(\d+)">')
_CARD_RE = re.compile(r"<app-pro-card.*?</app-pro-card>", re.S)
_CARD_LINK_RE = re.compile(
    r'<a[^>]*class="pro-card__link"[^>]*href="([^"]+)"')
_CARD_NAME_RE = re.compile(r'class="pro-card__name[^"]*"[^>]*>([^<]+)</h3>')
_CARD_PLACE_RE = re.compile(r'class="pro-card__place[^"]*"[^>]*>([^<]+)</h3>')
_CARD_DATE_RE = re.compile(r'class="pro-card__date[^"]*"[^>]*>([^<]+)</h3>')
_CARD_INFO_RE = re.compile(r'class="pro-card__info[^"]*"[^>]*>([^<]*)</p>')
_PRO_COUNT_RE = re.compile(r"([\d.]+)\s+\S+\s+haz[ıi]r")
_SITEMAP_LOC_RE = re.compile(
    r"<loc>https://armut\.com/fiyatlari/([a-z0-9-]+)_(\d+)</loc>")
_TR_FOLD = str.maketrans({
    "ç": "c", "ğ": "g", "ı": "i", "ö": "o", "ş": "s", "ü": "u",
    "Ç": "c", "Ğ": "g", "İ": "i", "I": "i", "Ö": "o", "Ş": "s", "Ü": "u",
})


def _num(value) -> int | float | None:
    """Turkish-formatted number ('10.141', 5950000, '4,6') -> int/float."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return value
    s = str(value).strip().replace(".", "").replace(",", ".")
    try:
        f = float(s)
    except ValueError:
        return None
    return int(f) if f == int(f) else f


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", _html.unescape(text or "")).strip()


def _fold(value: str) -> str:
    """Lowercase + fold Turkish diacritics for matching."""
    return value.translate(_TR_FOLD).lower()


def extract_next_data(html_text: str) -> dict:
    """Parse the __NEXT_DATA__ JSON blob of a Next.js page (or {})."""
    m = _NEXT_DATA_RE.search(html_text)
    if not m:
        return {}
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return {}


def _ldjson_docs(html_text: str) -> list[dict]:
    docs: list[dict] = []
    for block in _LDJSON_RE.findall(html_text):
        try:
            doc = json.loads(block)
        except json.JSONDecodeError:
            continue
        if isinstance(doc, dict):
            docs.append(doc)
    return docs


def _ldjson_by_type(html_text: str, want: str) -> dict:
    for doc in _ldjson_docs(html_text):
        if doc.get("@type") == want:
            return doc
    return {}


# ---------------------------------------------------------------- homepage

def parse_homepage(next_data: dict) -> dict:
    """Homepage __NEXT_DATA__ -> groups, trending/popular, most-searched."""
    data = next_data.get("props", {}).get("pageProps", {}).get("data", {})

    def _svc(s: dict) -> dict:
        return {
            "service_id": s.get("serviceId"),
            "name": s.get("name", ""),
            "slug": s.get("slug", ""),
            "pro_count": s.get("proCount"),
            "rating_average": s.get("ratingAverage"),
            "verified_reviews": s.get("verifiedReviewsCount"),
        }

    services = data.get("services", {}) or {}
    return {
        "service_groups": [
            {"group_id": g.get("groupId"), "name": g.get("name", ""),
             "slug": g.get("slug", "")}
            for g in data.get("serviceGroups", []) or []
        ],
        "trending": [_svc(s) for s in services.get("trending", []) or []],
        "popular": [_svc(s) for s in services.get("popular", []) or []],
        "most_searched": [
            {"service": s.get("serviceName", ""),
             "city": s.get("areaLevel1Name", ""), "slug": s.get("slug", "")}
            for s in services.get("mostSearched", []) or []
        ],
        "near_me_cities": [
            {"city": s.get("areaLevel1Name", ""), "slug": s.get("slug", "")}
            for s in services.get("nearMe", []) or []
        ],
    }


# ------------------------------------------------------------ service page

def parse_service_id(html_text: str) -> int | None:
    m = _SERVICE_ID_RE.search(html_text)
    return int(m.group(1)) if m else None


def parse_service_detail(html_text: str) -> dict:
    """Service page -> Product JSON-LD + service id + pro count."""
    product = _ldjson_by_type(html_text, "Product")
    if not product:
        return {"error": "no service data found on this page"}
    rating = product.get("aggregateRating") or {}
    description = _clean(product.get("description", ""))
    pro_count = None
    pm = _PRO_COUNT_RE.search(description)
    if pm:
        pro_count = _num(pm.group(1))
    return {
        "name": _clean(product.get("name", "")),
        "description": description,
        "image": product.get("image") or "",
        "url": product.get("url") or "",
        "service_id": parse_service_id(html_text),
        "pro_count": pro_count,
        "rating_average": rating.get("ratingValue"),
        "review_count": rating.get("reviewCount"),
    }


def parse_pros(html_text: str, limit: int = 10) -> list[dict]:
    """Pros of a service page: rendered cards joined with ItemList ratings.

    The JSON-LD ItemList (37 on the captured page) and the rendered cards
    (40) do not line up 1:1, so ratings are joined by profile URL and a
    card without a rating still comes through with rating None.
    """
    ratings: dict[str, dict] = {}
    item_list = _ldjson_by_type(html_text, "ItemList")
    for el in item_list.get("itemListElement", []) or []:
        item = el.get("item", {}) if isinstance(el, dict) else {}
        url = item.get("url") or ""
        agg = item.get("aggregateRating") or {}
        if url:
            ratings[url] = {
                "rating": agg.get("ratingValue"),
                "review_count": agg.get("ratingCount"),
            }
    out: list[dict] = []
    for card in _CARD_RE.findall(html_text):
        link = _CARD_LINK_RE.search(card)
        name = _CARD_NAME_RE.search(card)
        place = _CARD_PLACE_RE.search(card)
        date = _CARD_DATE_RE.search(card)
        info = _CARD_INFO_RE.search(card)
        url = link.group(1) if link else ""
        place_text = _clean(place.group(1)) if place else ""
        # place looks like "Ev Temizliği · Altıeylül, Balıkesir"
        location = place_text.split("·")[-1].strip() if "·" in place_text \
            else place_text
        r = ratings.get(url, {})
        out.append({
            "name": _clean(name.group(1)) if name else "",
            "location": location,
            "since": _clean(date.group(1)) if date else "",
            "bio": _clean(info.group(1))[:300] if info else "",
            "rating": r.get("rating"),
            "review_count": r.get("review_count"),
            "profile_url": url,
        })
        if len(out) >= limit:
            break
    return out


def parse_faq(html_text: str) -> list[dict]:
    """FAQPage JSON-LD -> [{question, answer}]."""
    faq = _ldjson_by_type(html_text, "FAQPage")
    out: list[dict] = []
    for q in faq.get("mainEntity", []) or []:
        if not isinstance(q, dict):
            continue
        ans = q.get("acceptedAnswer") or {}
        out.append({
            "question": _clean(q.get("name", "")),
            "answer": _clean(ans.get("text", "")),
        })
    return out


# -------------------------------------------------------------- price page

def parse_price_page(next_data: dict) -> dict:
    """Price-guide __NEXT_DATA__ -> compact price guide."""
    data = (next_data.get("props", {}).get("pageProps", {})
            .get("data", {}).get("pricePageData", {}))
    if not data:
        return {"error": "no price data found on this page"}
    monthly = [{
        "month": m.get("month", "")[:7],
        "avg_try": m.get("avgPrice"),
        "min_try": m.get("minPrice"),
        "max_try": m.get("maxPrice"),
        "quotes": m.get("quoteCount"),
    } for m in data.get("monthlyPrices", []) or []]
    jobs = [{
        "date": j.get("date", ""),
        "area": ", ".join(x for x in [
            j.get("jobAreaLevel2Name", ""), j.get("jobAreaLevel1Name", "")]
            if x),
        "details": _clean(j.get("jobDetails", ""))[:200],
        "min_quote_try": j.get("minQuotePrice"),
        "max_quote_try": j.get("maxQuotePrice"),
        "winning_try": j.get("winnerPrice"),
    } for j in (data.get("exampleJobs", []) or [])[:5]]
    reviews = [{
        "name": r.get("displayName", ""),
        "date": r.get("date", ""),
        "rating": r.get("rating"),
        "review": _clean(r.get("review", ""))[:300],
    } for r in (data.get("consumerReviews", []) or [])[:3]]
    return {
        "service": data.get("serviceName", ""),
        "service_id": data.get("serviceId"),
        "city": data.get("areaLevel1Name") or "Türkiye geneli",
        "currency": "TRY",
        "min_price_try": data.get("minPrice"),
        "max_price_try": data.get("maxPrice"),
        "quote_count": data.get("quoteCount"),
        "pro_count": data.get("proCount"),
        "rating_average": data.get("ratingAvg"),
        "rating_count": data.get("ratingCount"),
        "monthly_average_try": monthly,
        "example_jobs": jobs,
        "reviews": reviews,
        "district_price_pages": [
            {"district": p.get("areaLevel2Name", ""), "url":
             f"https://armut.com/{p.get('url', '')}"}
            for p in (data.get("regionalPricePages", []) or [])
        ],
        "price_page_url": (
            f"https://armut.com/{data.get('url', '')}"
            if data.get("url") else ""),
    }


# ------------------------------------------------------------------ search

def parse_price_sitemap(xml_text: str) -> list[dict]:
    """Price sitemap -> full service catalogue [{slug, service_id, url}]."""
    out: list[dict] = []
    for slug, sid in _SITEMAP_LOC_RE.findall(xml_text):
        out.append({
            "slug": slug,
            "name": slug.replace("-", " ").title(),
            "service_id": int(sid),
            "price_url": f"https://armut.com/fiyatlari/{slug}_{sid}",
            "service_url": f"https://armut.com/{slug}",
        })
    return out


def search_services(entries: list[dict], query: str,
                    limit: int = 10) -> list[dict]:
    """Turkish-insensitive substring search over the service catalogue.

    Matches the query against the slug and the spaced-out service name
    ('ev temizligi' matches 'ev-temizligi'); results are ordered with
    slug-prefix matches first, then the rest in catalogue order.

    Turkish -lik nouns surface as -ligi in slugs ('temizlik' ->
    'ev-temizligi'), so a query ending in 'k' is also tried with the
    'k' -> 'gi' ending ('temizlik' also matches 'ev-temizligi').
    """
    q = _fold(query.strip())
    if not q:
        return []
    variants = {q}
    if q.endswith("k"):
        variants.add(q[:-1] + "gi")
    scored: list[tuple[int, dict]] = []
    for e in entries:
        slug = _fold(e["slug"])
        name = _fold(e["slug"].replace("-", " "))
        if any(v in slug or v in name for v in variants):
            score = 0 if any(slug.startswith(v) for v in variants) else 1
            scored.append((score, e))
    scored.sort(key=lambda t: t[0])
    return [e for _, e in scored[:max(1, min(int(limit), 20))]]
