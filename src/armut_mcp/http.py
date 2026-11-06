"""HTTP layer for armut_mcp — polite reads of public Armut pages.

armut.com serves server-rendered pages with no bot wall (verified live
2026-11-06 with plain curl + a browser UA): service data comes from
embedded schema.org JSON-LD (Product + ItemList of pros + FAQPage) on
service pages, from __NEXT_DATA__ on the homepage and on /fiyatlari/
price-guide pages, and from the public price sitemap for the full
service catalogue. We keep requests gentle (one at a time, ~0.8s apart)
and read-only.

URL scheme (verified live 2026-11-06):
  /                                  homepage (__NEXT_DATA__: service
                                     groups, trending/popular services,
                                     most-searched city+service combos)
  /{service-slug}                    service page (JSON-LD Product,
                                     ItemList of pros, FAQPage; hidden
                                     input #serviceId)
  /{city}-{service-slug}             same page, pros filtered to a city
                                     (e.g. /istanbul-ev-temizligi)
  /fiyatlari/{slug}_{serviceId}      price guide, all Türkiye
                                     (__NEXT_DATA__ pricePageData: min/
                                     max, 12 monthly averages, quotes,
                                     example jobs, reviews)
  /fiyatlari/{city}-{slug}_{serviceId}_1
                                     price guide for one city
  /sitemap/price-1.xml               full service catalogue:
                                     6,759 /fiyatlari/{slug}_{id} URLs
"""
from __future__ import annotations

import os
import re
import time

import httpx

BASE = "https://armut.com"
UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)
TIMEOUT = 30.0
MIN_INTERVAL = 0.8  # seconds between requests — be polite

_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
# Turkish chars folded to ASCII for slug validation of city names typed
# with diacritics (e.g. "İstanbul" -> "istanbul").
_TR_FOLD = str.maketrans({
    "ç": "c", "ğ": "g", "ı": "i", "ö": "o", "ş": "s", "ü": "u",
    "Ç": "c", "Ğ": "g", "İ": "i", "I": "i", "Ö": "o", "Ş": "s", "Ü": "u",
})

_last_fetch = 0.0


class ArmutError(RuntimeError):
    pass


def _client() -> httpx.Client:
    # NOTE: proxy URL is read from the environment but never logged.
    # trust_env=False because httpx fails to parse bracketed IPv6 entries
    # (e.g. [::1]) that some environments put in no_proxy.
    proxy = os.environ.get("https_proxy") or os.environ.get("HTTPS_PROXY")
    # Standard SSL_CERT_FILE convention lets MITM-proxied environments
    # point at a CA bundle that trusts the proxy; default uses certifi,
    # which is correct for normal users.
    verify: object = True
    cafile = os.environ.get("SSL_CERT_FILE")
    if cafile:
        import ssl

        verify = ssl.create_default_context(cafile=cafile)
    return httpx.Client(
        headers={"User-Agent": UA, "Accept-Language": "tr-TR,tr;q=0.9"},
        timeout=TIMEOUT,
        proxy=proxy or None,
        verify=verify,
        trust_env=False,
        follow_redirects=True,
    )


def fold_tr(value: str) -> str:
    """Fold Turkish diacritics to ASCII ('İstanbul' -> 'istanbul')."""
    return value.translate(_TR_FOLD)


def _slug(value: str, what: str) -> str:
    s = fold_tr(value.strip()).lower()
    if not _SLUG_RE.fullmatch(s):
        raise ArmutError(
            f"bad {what} slug: {value!r} — use lowercase letters, digits "
            "and dashes, e.g. 'ev-temizligi', 'istanbul'")
    return s


def service_url(service_slug: str, city: str = "") -> str:
    slug = _slug(service_slug, "service")
    if city:
        return f"{BASE}/{_slug(city, 'city')}-{slug}"
    return f"{BASE}/{slug}"


def price_url(service_slug: str, service_id: int, city: str = "") -> str:
    slug = _slug(service_slug, "service")
    if int(service_id) <= 0:
        raise ArmutError(f"bad service id: {service_id!r}")
    if city:
        return f"{BASE}/fiyatlari/{_slug(city, 'city')}-{slug}_{service_id}_1"
    return f"{BASE}/fiyatlari/{slug}_{service_id}"


def fetch(url: str) -> str:
    """GET a page; raises ArmutError on failure or bot-wall."""
    global _last_fetch
    wait = MIN_INTERVAL - (time.monotonic() - _last_fetch)
    if wait > 0:
        time.sleep(wait)
    try:
        with _client() as c:
            r = c.get(url)
    except httpx.HTTPError as e:
        raise ArmutError(f"network error fetching {url}: {e}") from e
    _last_fetch = time.monotonic()
    if r.status_code == 404:
        raise ArmutError(
            f"armut.com returned HTTP 404 for {url} — check the slug "
            "(use armut_search_services to find valid service slugs)")
    if r.status_code != 200:
        raise ArmutError(f"armut.com returned HTTP {r.status_code} for {url}")
    text = r.text
    if "PerimeterX" in text or "px-captcha" in text or "Cloudflare" in text:
        raise ArmutError("armut.com is showing a bot check for this request")
    return text


def fetch_home() -> str:
    return fetch(f"{BASE}/")


def fetch_service(service_slug: str, city: str = "") -> str:
    return fetch(service_url(service_slug, city))


def fetch_price(service_slug: str, service_id: int, city: str = "") -> str:
    return fetch(price_url(service_slug, service_id, city))


def fetch_price_sitemap() -> str:
    return fetch(f"{BASE}/sitemap/price-1.xml")
