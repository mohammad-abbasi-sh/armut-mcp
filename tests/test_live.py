"""Live tests — hit the real armut.com. Cautious: a handful of requests,
spaced ~0.8s apart by the http layer.

Run:  pytest tests/test_live.py -v
Skip: pytest -m "not live"  (or set ARMUT_SKIP_LIVE=1)
"""
import os
import pathlib
import sys
import unittest

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from armut_mcp import http as _H
from armut_mcp import services as _S

pytestmark = pytest.mark.live
SKIP = os.environ.get("ARMUT_SKIP_LIVE") == "1"


@pytest.mark.skipif(SKIP, reason="ARMUT_SKIP_LIVE=1")
class TestLive(unittest.TestCase):
    def test_search_live(self):
        xml = _H.fetch_price_sitemap()
        entries = _S.parse_price_sitemap(xml)
        self.assertGreater(len(entries), 1000, "catalogue should be big")
        rows = _S.search_services(entries, "temizlik", limit=20)
        self.assertGreater(len(rows), 10, "many cleaning services exist")
        exact = _S.search_services(entries, "ev-temizligi")
        self.assertEqual(exact[0]["slug"], "ev-temizligi")
        self.assertEqual(exact[0]["service_id"], 191)
        print(f"\nLIVE: {len(entries)} services in catalogue; "
              f"'temizlik' -> {len(rows)} shown")

    def test_service_detail_live(self):
        html = _H.fetch_service("ev-temizligi")
        d = _S.parse_service_detail(html)
        self.assertEqual(d["name"], "Ev Temizliği")
        self.assertEqual(d["service_id"], 191)
        self.assertGreater(d["pro_count"], 1000)
        self.assertGreater(d["rating_average"], 4.0)
        self.assertGreater(d["review_count"], 100000)
        print(f"\nLIVE detail: {d['name']} | {d['pro_count']:,} pros | "
              f"{d['rating_average']}★ ({d['review_count']:,} reviews)")

    def test_pros_live(self):
        html = _H.fetch_service("ev-temizligi")
        pros = _S.parse_pros(html, limit=5)
        self.assertGreater(len(pros), 0)
        for p in pros:
            self.assertTrue(p["name"])
            self.assertTrue(p["profile_url"].startswith(
                "https://armut.com/hizmetveren/"))
        print(f"\nLIVE pros: {pros[0]['name']} — {pros[0]['location']} — "
              f"{pros[0]['rating']}★ ({pros[0]['review_count']} reviews)")

    def test_city_pros_live(self):
        html = _H.fetch_service("ev-temizligi", city="istanbul")
        pros = _S.parse_pros(html, limit=5)
        self.assertGreater(len(pros), 0)
        for p in pros:
            self.assertIn("İstanbul", p["location"])
        print(f"\nLIVE Istanbul pros: {pros[0]['name']} — "
              f"{pros[0]['location']}")

    def test_faq_live(self):
        html = _H.fetch_service("ev-temizligi")
        faqs = _S.parse_faq(html)
        self.assertGreater(len(faqs), 0)
        self.assertTrue(all(f["question"] and f["answer"] for f in faqs))
        print(f"\nLIVE FAQ: {len(faqs)} questions; first: "
              f"{faqs[0]['question'][:60]}")

    def test_price_guide_live(self):
        html = _H.fetch_service("ev-temizligi")
        sid = _S.parse_service_id(html)
        page = _H.fetch_price("ev-temizligi", sid)
        g = _S.parse_price_page(_S.extract_next_data(page))
        self.assertEqual(g["service"], "Ev Temizliği")
        self.assertEqual(len(g["monthly_average_try"]), 12)
        self.assertGreater(g["quote_count"], 0)
        latest = g["monthly_average_try"][0]
        print(f"\nLIVE price guide: latest month {latest['month']} avg "
              f"{latest['avg_try']:,.0f} TRY over {latest['quotes']} quotes; "
              f"{g['quote_count']:,} quotes total")

    def test_city_price_guide_live(self):
        html = _H.fetch_service("ev-temizligi")
        sid = _S.parse_service_id(html)
        page = _H.fetch_price("ev-temizligi", sid, city="adana")
        g = _S.parse_price_page(_S.extract_next_data(page))
        self.assertEqual(g["city"], "Adana")
        self.assertGreater(g["quote_count"], 0)
        print(f"\nLIVE Adana price guide: {g['quote_count']:,} quotes; "
              f"min {g['min_price_try']} / max {g['max_price_try']} TRY")

    def test_trending_live(self):
        html = _H.fetch_home()
        data = _S.parse_homepage(_S.extract_next_data(html))
        self.assertGreater(len(data["trending"]), 0)
        self.assertGreater(len(data["popular"]), 0)
        self.assertGreater(len(data["service_groups"]), 0)
        print(f"\nLIVE trending: {data['trending'][0]['name']} "
              f"({data['trending'][0]['pro_count']:,} pros); "
              f"{len(data['popular'])} popular services")


if __name__ == "__main__":
    unittest.main()
