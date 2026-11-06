"""Offline tests — parse real captured armut.com fixtures (no network)."""
import json
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from armut_mcp import http as _H
from armut_mcp import services as _S

FIX = pathlib.Path(__file__).resolve().parent / "fixtures"


class TestHomepage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = json.loads((FIX / "home_nextdata.json").read_text())
        cls.data = _S.parse_homepage(cls.doc)

    def test_service_groups(self):
        self.assertEqual(len(self.data["service_groups"]), 6)
        self.assertEqual(self.data["service_groups"][0]["name"], "Temizlik")
        self.assertEqual(self.data["service_groups"][0]["slug"], "temizlik")

    def test_trending_first(self):
        t = self.data["trending"]
        self.assertEqual(len(t), 12)
        self.assertEqual(t[0]["name"], "Evden Eve Nakliyat")
        self.assertEqual(t[0]["service_id"], 142)
        self.assertEqual(t[0]["slug"], "evden-eve-nakliyat")
        self.assertEqual(t[0]["pro_count"], 3093)
        self.assertEqual(t[0]["rating_average"], 4.9)
        self.assertEqual(t[0]["verified_reviews"], 205901)

    def test_popular_count(self):
        self.assertEqual(len(self.data["popular"]), 24)
        self.assertEqual(self.data["popular"][0]["name"], "Boş Ev Temizliği")

    def test_most_searched(self):
        ms = self.data["most_searched"]
        self.assertEqual(len(ms), 8)
        self.assertEqual(ms[0]["city"], "İstanbul")
        self.assertEqual(ms[0]["service"], "Boş Ev Temizliği")

    def test_empty_next_data(self):
        self.assertEqual(_S.parse_homepage({})["trending"], [])
        self.assertEqual(_S.extract_next_data("<html></html>"), {})


class TestServiceDetail(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (FIX / "service_page.html").read_text()

    def test_detail_fields(self):
        d = _S.parse_service_detail(self.html)
        self.assertEqual(d["name"], "Ev Temizliği")
        self.assertEqual(d["service_id"], 191)
        self.assertEqual(d["pro_count"], 10141)
        self.assertEqual(d["rating_average"], 4.6)
        self.assertEqual(d["review_count"], 415591)
        self.assertTrue(d["description"].startswith("Güvenilir Ev Temizliği"))
        self.assertTrue(d["url"].endswith("/ev-temizligi"))

    def test_service_id_extraction(self):
        self.assertEqual(_S.parse_service_id(self.html), 191)
        self.assertIsNone(_S.parse_service_id("<html></html>"))

    def test_no_data_returns_error(self):
        self.assertIn("error", _S.parse_service_detail("<html></html>"))


class TestPros(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (FIX / "service_page.html").read_text()
        cls.city_html = (FIX / "city_service_page.html").read_text()

    def test_first_pro_fields(self):
        p = _S.parse_pros(self.html, limit=10)[0]
        self.assertEqual(p["name"], "Alime C.")
        self.assertEqual(p["location"], "Altıeylül, Balıkesir")
        self.assertEqual(p["since"], "02.03.2021")
        self.assertEqual(p["rating"], 4.4)
        self.assertEqual(p["review_count"], 464)
        self.assertTrue(p["profile_url"].endswith("_3694478"))
        self.assertTrue(p["bio"].startswith("İşimi severek yapıyorum"))

    def test_limit_respected(self):
        self.assertEqual(len(_S.parse_pros(self.html, limit=2)), 2)

    def test_city_page_pros_are_istanbul(self):
        pros = _S.parse_pros(self.city_html, limit=3)
        self.assertEqual(pros[0]["name"], "Nermin K.")
        for p in pros:
            self.assertIn("İstanbul", p["location"])

    def test_city_detail_review_count_differs(self):
        d = _S.parse_service_detail(self.city_html)
        self.assertEqual(d["review_count"], 218197)


class TestFaq(unittest.TestCase):
    def test_faq_parsed(self):
        html = (FIX / "service_page.html").read_text()
        faqs = _S.parse_faq(html)
        self.assertEqual(len(faqs), 6)
        self.assertEqual(faqs[0]["question"], "1- Temizliğe Neler Dahil?")
        self.assertIn("Standart temizlik", faqs[0]["answer"])

    def test_no_faq_returns_empty(self):
        self.assertEqual(_S.parse_faq("<html></html>"), [])


class TestPricePage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = json.loads((FIX / "price_nextdata.json").read_text())
        cls.guide = _S.parse_price_page(cls.doc)

    def test_guide_fields(self):
        g = self.guide
        self.assertEqual(g["service"], "Ev Temizliği")
        self.assertEqual(g["service_id"], 191)
        self.assertEqual(g["city"], "Adana")
        self.assertEqual(g["min_price_try"], 479)
        self.assertEqual(g["max_price_try"], 1024)
        self.assertEqual(g["quote_count"], 745)
        self.assertEqual(g["pro_count"], 435)
        self.assertEqual(g["rating_average"], 4.6)
        self.assertEqual(g["rating_count"], 16984)
        self.assertEqual(g["currency"], "TRY")

    def test_monthly_averages(self):
        m = self.guide["monthly_average_try"]
        self.assertEqual(len(m), 12)
        self.assertEqual(m[0]["month"], "2025-11")
        self.assertAlmostEqual(m[0]["avg_try"], 2756.39, places=1)
        self.assertEqual(m[0]["min_try"], 1763)
        self.assertEqual(m[0]["max_try"], 3806)
        self.assertEqual(m[0]["quotes"], 88)

    def test_example_jobs_and_reviews(self):
        jobs = self.guide["example_jobs"]
        self.assertEqual(len(jobs), 5)
        self.assertEqual(jobs[0]["winning_try"], 3840)
        self.assertIn("Adana", jobs[0]["area"])
        self.assertEqual(len(self.guide["reviews"]), 3)
        self.assertEqual(self.guide["reviews"][0]["name"], "Dilek K.")
        self.assertEqual(self.guide["reviews"][0]["rating"], 5)

    def test_district_pages(self):
        dps = self.guide["district_price_pages"]
        self.assertEqual(len(dps), 3)
        self.assertEqual(dps[0]["district"], "Seyhan")
        self.assertTrue(dps[0]["url"].startswith("https://armut.com/fiyatlari-ilce/"))

    def test_no_data_returns_error(self):
        self.assertIn("error", _S.parse_price_page({}))

    def test_extract_next_data_roundtrip(self):
        # Next.js escapes "<" as \u003c inside __NEXT_DATA__ (the embedded
        # HTML in customContent contains "</script>" otherwise).
        blob = json.dumps(self.doc, ensure_ascii=False).replace("<", "\\u003c")
        html = ('<html><head><script id="__NEXT_DATA__" '
                f'type="application/json">{blob}</script></head></html>')
        self.assertEqual(_S.extract_next_data(html), self.doc)


class TestSearch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        xml = (FIX / "price_sitemap.xml").read_text()
        cls.entries = _S.parse_price_sitemap(xml)

    def test_sitemap_parsed(self):
        self.assertEqual(len(self.entries), 15)
        ev = [e for e in self.entries if e["slug"] == "ev-temizligi"][0]
        self.assertEqual(ev["service_id"], 191)
        self.assertEqual(ev["price_url"],
                         "https://armut.com/fiyatlari/ev-temizligi_191")
        self.assertEqual(ev["service_url"], "https://armut.com/ev-temizligi")

    def test_turkish_query(self):
        rows = _S.search_services(self.entries, "temizlik")
        self.assertEqual(len(rows), 10)  # all 10 temizlik matches
        slugs = [r["slug"] for r in rows]
        # -lik nouns surface as -ligi in slugs: ev-temizligi must match too
        self.assertIn("ev-temizligi", slugs)
        self.assertIn("bos-ev-temizligi", slugs)

    def test_exact_slug_first(self):
        rows = _S.search_services(self.entries, "ev-temizligi")
        self.assertEqual(rows[0]["slug"], "ev-temizligi")
        self.assertEqual(rows[1]["slug"], "bos-ev-temizligi")

    def test_turkish_chars_folded(self):
        rows = _S.search_services(self.entries, "TEMİZLİK")
        self.assertGreater(len(rows), 0)
        rows2 = _S.search_services(self.entries, "nakliyat")
        self.assertEqual(len(rows2), 4)

    def test_no_match_and_empty(self):
        self.assertEqual(_S.search_services(self.entries, "zzzqqq"), [])
        self.assertEqual(_S.search_services(self.entries, "  "), [])
        self.assertEqual(len(_S.search_services(self.entries, "temizlik",
                                                limit=3)), 3)


class TestUrls(unittest.TestCase):
    def test_service_url(self):
        self.assertEqual(_H.service_url("ev-temizligi"),
                         "https://armut.com/ev-temizligi")
        self.assertEqual(_H.service_url("ev-temizligi", city="istanbul"),
                         "https://armut.com/istanbul-ev-temizligi")

    def test_price_url(self):
        self.assertEqual(_H.price_url("ev-temizligi", 191),
                         "https://armut.com/fiyatlari/ev-temizligi_191")
        self.assertEqual(_H.price_url("ev-temizligi", 191, city="adana"),
                         "https://armut.com/fiyatlari/adana-ev-temizligi_191_1")

    def test_bad_slug_rejected(self):
        with self.assertRaises(_H.ArmutError):
            _H.service_url("../../etc")
        with self.assertRaises(_H.ArmutError):
            _H.price_url("ev-temizligi", 0)
        with self.assertRaises(_H.ArmutError):
            _H.service_url("ev-temizligi", city="is tanbul")

    def test_turkish_city_folded(self):
        self.assertEqual(_H.service_url("ev-temizligi", city="İstanbul"),
                         "https://armut.com/istanbul-ev-temizligi")


if __name__ == "__main__":
    unittest.main()
