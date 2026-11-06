# armut-mcp 🇹🇷

سرور MCP غیررسمی و **فقط‌خواندنی** برای **armut.com**، بازار خدمات محلی ترکیه — جست‌وجو در ۶٬۷۵۹ خدمت (نظافت، اسباب‌کشی، تعمیرات، تدریس خصوصی و بیشتر)، مرور بهترین متخصصان با امتیاز و نظر، پرسش‌های متداول هر خدمت و راهنمای قیمت با میانگین ۱۲ ماهه و نمونه‌های واقعی قیمت‌ها.

> ساختهٔ محمد عباسی در قالب «کارخانهٔ Turkey MCP» (خط تولید به سبک سپهر). وابستگی به armut.com ندارد.

## برای ایجنت‌های هوش مصنوعی

به پیکربندی کلاینت MCP خود (stdio) اضافه کنید:

```json
{
  "mcpServers": {
    "armut": {
      "command": "uvx",
      "args": ["armut-mcp"]
    }
  }
}
```

یا به‌صورت محلی اجرا کنید: `python -m armut_mcp.server` (نیازمند `mcp<2` و `httpx`).

## ابزارها

| ابزار | توضیح |
|------|-------|
| `armut_search_services` | جست‌وجو در کاتالوگ ۶٬۷۵۹ خدمتی با کلیدواژه — `query` مثل «temizlik» (نظافت)، «nakliyat» (اسباب‌کشی)، «boyaci» (نقاش)؛ حروف ترکی مشکلی ندارند؛ نام کوتاه، شناسهٔ خدمت، آدرس راهنمای قیمت و صفحهٔ خدمت را برمی‌گرداند |
| `armut_service_detail` | جزئیات یک خدمت (نام کوتاه مثل «ev-temizligi»): نام، توضیح، تعداد متخصص، میانگین امتیاز، تعداد نظر، شناسهٔ خدمت |
| `armut_list_pros` | بهترین متخصصان یک خدمت: نام، شهر/منطقه، تاریخ عضویت، معرفی، امتیاز، تعداد نظر، آدرس پروفایل؛ `city` (مثل «istanbul») به آن شهر محدود می‌کند؛ `limit` از ۱ تا ۴۰ |
| `armut_service_faq` | پرسش‌های متداول یک خدمت با پاسخ‌ها |
| `armut_price_guide` | راهنمای قیمت یک خدمت: کمینه/بیشینهٔ قیمت در صفحه (لیر)، میانگین/کمینه/بیشینهٔ ۱۲ ماهه با تعداد قیمت‌ها، مجموع قیمت‌ها و متخصصان، امتیاز، نمونه‌های واقعی کار با قیمت برنده و نظرات اخیر مشتریان؛ `city` (مثل «adana») راهنمای آن شهر را می‌دهد |
| `armut_trending_services` | محبوب‌های الان: گروه‌های خدمت، خدمات ترند و محبوب با تعداد متخصص و امتیاز، پرجست‌وجوترین ترکیب‌های شهر+خدمت |

خروجی نمونه (`armut_search_services` / «temizlik»):

```json
{"query": "temizlik", "count": 10, "services": [
  {"slug": "ev-temizligi", "name": "Ev Temizligi", "service_id": 191,
   "price_url": "https://armut.com/fiyatlari/ev-temizligi_191",
   "service_url": "https://armut.com/ev-temizligi"}, …]}
```

خروجی نمونه (`armut_service_detail` / «ev-temizligi»):

```json
{"name": "Ev Temizliği", "service_id": 191, "pro_count": 10141,
 "rating_average": 4.6, "review_count": 415591,
 "description": "Güvenilir Ev Temizliği hizmeti al, zaman kazan, garantide ol. …",
 "url": "https://armut.com/ev-temizligi"}
```

خروجی نمونه (`armut_list_pros` / «ev-temizligi»، استانبول، ۱):

```json
{"service": "Ev Temizliği", "city": "istanbul", "count": 1, "pros": [
  {"name": "Nermin K.", "location": "Şişli, İstanbul", "since": "…",
   "bio": "…", "rating": 4.1, "review_count": 162,
   "profile_url": "https://armut.com/hizmetveren/…"}]}
```

خروجی نمونه (`armut_price_guide` / «ev-temizligi»، آدانا):

```json
{"service": "Ev Temizliği", "service_id": 191, "city": "Adana",
 "currency": "TRY", "min_price_try": 479, "max_price_try": 1024,
 "quote_count": 790, "pro_count": 433, "rating_average": 4.6,
 "monthly_average_try": [
  {"month": "2025-11", "avg_try": 2756.39, "min_try": 1763,
   "max_try": 3806, "quotes": 88}, …]}
```

نکته‌ها:
- داده‌ها از صفحات عمومی سمت‌سرور armut.com می‌آیند (JSON-LD از نوع Product/ItemList/FAQPage در schema.org در صفحات خدمت، `__NEXT_DATA__` در صفحهٔ اصلی و صفحات راهنمای قیمت، و نقشهٔ سایت عمومی قیمت) — بدون کلید، بدون ورود، فقط خواندنی.
- در ترکی، اسم‌های پایان‌یافته به `-lik` در نام‌های کوتاه به `-ligi` تبدیل می‌شوند («temizlik» ← «ev-temizligi»)؛ جست‌وجو این را در نظر می‌گیرد، پس جست‌وجوی سادهٔ «temizlik»، «ev-temizligi» را هم پیدا می‌کند.
- کمینه/بیشینهٔ قیمت صفحه و میانگین‌های ۱۲ ماهه از فیلدهای متفاوتی در صفحه می‌آیند؛ میانگین‌های ماهانه (همراه با تعداد قیمت‌ها) نشانهٔ قابل‌اعتمادتری برای قیمت‌اند.
- بین درخواست‌ها حدود ۰٫۸ ثانیه فاصله گذاشته می‌شود تا به سایت فشار نیاید.
- پشت پروکسی MITM: متغیر `SSL_CERT_FILE` را به بستهٔ CA مورد اعتماد پروکسی بدهید.

## توسعه

```bash
python3 -m venv .venv && .venv/bin/pip install "mcp<2" httpx pytest
.venv/bin/pip install -e .
.venv/bin/python -m pytest tests/ -q
```

- `tests/test_services.py` — آفلاین، با نمونه‌های واقعی ذخیره‌شده (۲۹ تست)
- `tests/test_live.py` — ۸ درخواست محتاطانهٔ زنده به armut.com

## مجوز

MIT
