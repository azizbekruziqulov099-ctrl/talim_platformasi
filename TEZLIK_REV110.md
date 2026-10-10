# REV110: 100 ming bola bir vaqtda kirganda sayt qotmasligi

## Kodda qilingan
- `modules/tez_kesh.py` — jarayon ichidagi kesh. Bitta dars 1000 marta bir soniyada so'ralsa ham bazaga BITTA so'rov
  boradi (qolganlari shu javobni kutadi). Dars 120 soniya keshda turadi (`DARS_CACHE_SEC`).
- `/api/ai_miya_media/<id>` — rasm har worker xotirasida (48 MB gacha, `MEDIA_CACHE_MB`), `ETag` + `304` javobi,
  `Cache-Control: public, max-age=31536000, immutable`. Rasm o'zgarmaydi: yangi miya yuklansa yangi id oladi.
- Bola ovozi serverga yuborilmaydi (faqat telefon xotirasida) — server yuklamasi oshmaydi.

## Cloudflare'da 2 ta qoida (bir marta, 5 daqiqa)
Cloudflare → saytingiz → **Caching → Cache Rules → Create rule**:

1. **Dars rasmlari**
   - If: `URI Path` *starts with* `/api/ai_miya_media/`
   - Then: **Eligible for cache**; Edge TTL — *Use cache-control header if present*; Browser TTL — *Respect origin*.
2. **Sayt fayllari (JS, CSS, rasm)**
   - If: `URI Path` *starts with* `/assets/`
   - Then: **Eligible for cache**; Edge TTL — *1 year*.

Natija: rasm va dastur fayllarini Cloudflare beradi, server faqat dars matni va javoblarni oladi.

## Eslatma
- Yangi miya yuklangandan keyin u saytda ko'pi bilan 2 daqiqada ko'rinadi (kesh muddati).
- Yuklama testi (k6 yoki Locust) bilan 1 000 → 10 000 → 100 000 bir vaqtdagi foydalanuvchini sinab ko'rish tavsiya
  etiladi; eng og'ir joy — kirish (sessiya tekshiruvi) va javoblarni yozish.
