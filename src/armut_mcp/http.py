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

import re
import time


BASE = "https://armut.com"

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


from curl_cffi import requests as _r

_HEADERS = {
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


_PROFILES = ("chrome120", "chrome131", "safari17_0")
_MAX_ATTEMPTS = 2  # one retry with the next profile
_RETRY_BACKOFF = 1.0  # seconds between attempts
_profile_idx = 0  # sticky: profile that last succeeded


def _request(url: str, headers: dict, timeout: float = TIMEOUT):
    """GET with fingerprint rotation.

    Starts at the sticky profile (chrome120 on a fresh process), retries
    once with the next profile on HTTP 403/429 or a transport error, then
    returns the last response (so the caller raises the specific 403/429
    error) or raises a network error if every attempt failed at the
    transport. Added 2026-11-10 (fleet audit fix).
    """
    global _profile_idx
    last_exc: Exception | None = None
    for k in range(_MAX_ATTEMPTS):
        profile = _PROFILES[(_profile_idx + k) % len(_PROFILES)]
        try:
            resp = _r.get(url, impersonate=profile, headers=headers, timeout=timeout)
        except Exception as e:
            last_exc = e
            if k + 1 < _MAX_ATTEMPTS:
                time.sleep(_RETRY_BACKOFF)
                continue
            raise ArmutError(f"network error fetching {url}: {e}") from e
        if resp.status_code in (403, 429):
            if k + 1 < _MAX_ATTEMPTS:
                time.sleep(_RETRY_BACKOFF)
                continue
            return resp
        _profile_idx = (_profile_idx + k) % len(_PROFILES)
        return resp
    raise ArmutError(f"network error fetching {url}: {last_exc}") from last_exc


def fetch(url: str) -> str:
    """GET a page; raises ArmutError on failure or bot-wall."""
    global _last_fetch
    wait = MIN_INTERVAL - (time.monotonic() - _last_fetch)
    if wait > 0:
        time.sleep(wait)
    try:
        resp = _request(url, _HEADERS)
    except ArmutError:
        raise
    except Exception as e:
        raise ArmutError(f"network error fetching {url}: {e}") from e
    _last_fetch = time.monotonic()
    if resp.status_code == 403:
        raise ArmutError(
            "armut.com refused the request (HTTP 403, bot wall) — try again later"
        )
    if resp.status_code == 429:
        raise ArmutError(
            "armut.com rate-limited the request (HTTP 429) — try again later"
        )
    if resp.status_code == 404:
        raise ArmutError(
            f"armut.com returned HTTP 404 for {url} — check the slug "
            "(use armut_search_services to find valid service slugs)")
    if resp.status_code != 200:
        raise ArmutError(f"armut.com returned HTTP {resp.status_code} for {url}")
    text = resp.text
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


def health_check() -> dict:
    """One polite probe of the source site.

    Returns {"status": "ok"|"blocked"|"error", "http_status": int|None,
    "url": ..., "detail": ...}. Used by the `armut_health` tool
    and the daily smoke CI. Added 2026-11-10 (fleet audit fix).
    """
    url = "https://armut.com/"
    try:
        fetch_home()
    except ArmutError as e:
        msg = str(e)
        if "403" in msg:
            return {"status": "blocked", "http_status": 403, "url": url, "detail": msg}
        if "429" in msg:
            return {"status": "blocked", "http_status": 429, "url": url, "detail": msg}
        return {"status": "error", "http_status": None, "url": url, "detail": msg}
    return {"status": "ok", "http_status": 200, "url": url}
