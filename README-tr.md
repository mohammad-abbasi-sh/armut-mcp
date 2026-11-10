# armut-mcp 🇹🇷

Türkiye'nin yerel hizmetler pazaryeri **armut.com** için resmi olmayan, **salt okunur** MCP sunucusu — 6.759 hizmette arama (temizlik, nakliyat, tamir, özel ders ve daha fazlası), puan ve yorumlarıyla en iyi profesyoneller, hizmet SSS'leri ve 12 aylık ortalama fiyatlar ile gerçek teklif örnekleri içeren fiyat rehberleri.

> Mohammad Abbasi tarafından "Turkey MCP factory" (Sepehr tarzı hat) kapsamında geliştirildi. armut.com ile bağlantısı yoktur.

## Yapay zekâ ajanları için

MCP istemci yapılandırmanıza (stdio) ekleyin:

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

Veya yerelde çalıştırın: `python -m armut_mcp.server` (`mcp<2`, `httpx` gerekir).

## Araçlar

| Araç | Açıklama |
|------|----------|
| `armut_search_services` | 6.759 hizmetlik katalogda anahtar kelimeyle arama — `query` ("temizlik", "nakliyat", "boyaci"), Türkçe harfler sorun değil; kısaltma, hizmet kimliği, fiyat rehberi ve hizmet sayfası adresini döndürür |
| `armut_service_detail` | Tek hizmetin detayı (kısaltma, örn. "ev-temizligi"): ad, açıklama, profesyonel sayısı, ortalama puan, yorum sayısı, hizmet kimliği |
| `armut_list_pros` | Bir hizmetin en iyi profesyonelleri: ad, şehir/ilçe, üyelik tarihi, tanıtım yazısı, puan, yorum sayısı, profil adresi; `city` ("istanbul") o şehre filtreler; `limit` 1..40 |
| `armut_service_faq` | Bir hizmetin sık sorulan soruları ve cevapları |
| `armut_price_guide` | Bir hizmetin fiyat rehberi: sayfadaki en düşük/en yüksek fiyat (TL), 12 aylık ortalama/en düşük/en yüksek fiyatlar ve teklif sayıları, toplam teklif ve profesyonel sayısı, puan, kazanan fiyatlarıyla gerçek iş örnekleri, son müşteri yorumları; `city` ("adana") o şehrin rehberini verir |
| `armut_trending_services` | Şu an popüler olanlar: hizmet grupları, trend ve popüler hizmetler (profesyonel sayısı ve puanlarıyla), en çok aranan şehir+hizmet kombinasyonları |

Örnek çıktı (`armut_search_services` / "temizlik"):

```json
{"query": "temizlik", "count": 10, "services": [
  {"slug": "ev-temizligi", "name": "Ev Temizligi", "service_id": 191,
   "price_url": "https://armut.com/fiyatlari/ev-temizligi_191",
   "service_url": "https://armut.com/ev-temizligi"}, …]}
```

Örnek çıktı (`armut_service_detail` / "ev-temizligi"):

```json
{"name": "Ev Temizliği", "service_id": 191, "pro_count": 10141,
 "rating_average": 4.6, "review_count": 415591,
 "description": "Güvenilir Ev Temizliği hizmeti al, zaman kazan, garantide ol. …",
 "url": "https://armut.com/ev-temizligi"}
```

Örnek çıktı (`armut_list_pros` / "ev-temizligi", İstanbul, 1):

```json
{"service": "Ev Temizliği", "city": "istanbul", "count": 1, "pros": [
  {"name": "Nermin K.", "location": "Şişli, İstanbul", "since": "…",
   "bio": "…", "rating": 4.1, "review_count": 162,
   "profile_url": "https://armut.com/hizmetveren/…"}]}
```

Örnek çıktı (`armut_price_guide` / "ev-temizligi", Adana):

```json
{"service": "Ev Temizliği", "service_id": 191, "city": "Adana",
 "currency": "TRY", "min_price_try": 479, "max_price_try": 1024,
 "quote_count": 790, "pro_count": 433, "rating_average": 4.6,
 "monthly_average_try": [
  {"month": "2025-11", "avg_try": 2756.39, "min_try": 1763,
   "max_try": 3806, "quotes": 88}, …]}
```

Notlar:
- Veriler armut.com'un herkese açık sunucu taraflı sayfalarından gelir (hizmet sayfalarında schema.org Product/ItemList/FAQPage JSON-LD, ana sayfa ve fiyat rehberi sayfalarında `__NEXT_DATA__`, herkese açık fiyat site haritası) — anahtar yok, giriş yok, salt okunur.
- Türkçede `-lik` ile biten isimler kısaltmalarda `-ligi` olur ("temizlik" → "ev-temizligi"); arama bunu dikkate alır, yani düz "temizlik" sorgusu "ev-temizligi"ni de bulur.
- Sayfadaki en düşük/en yüksek fiyat ile 12 aylık ortalamalar sayfanın farklı alanlarından gelir; teklif sayılarıyla birlikte verilen aylık ortalamalar daha güvenilir fiyat göstergesidir.
- İstekler arasında ~0,8 sn beklenir (nazik kullanım).
- MITM proxy arkasındaki ortamlar: `SSL_CERT_FILE` ile proxy'ye güvenen bir CA paketi gösterin.

## Geliştirme

```bash
python3 -m venv .venv && .venv/bin/pip install "mcp<2" curl-cffi pytest
.venv/bin/pip install -e .
.venv/bin/python -m pytest tests/ -q
```

- `tests/test_services.py` — çevrimdışı, gerçek yakalanmış örneklerle (29 test)
- `tests/test_live.py` — armut.com'a karşı 8 temkinli canlı istek

## Lisans

MIT

---

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
