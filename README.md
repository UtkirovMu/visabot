# Turan Int. School — Viza holati boti

Telegram bot: `/start` bosilganda sayt haqida aytib beradi. Foydalanuvchi **kanalga obuna bo'lgandan keyin** [viza holatini tekshirish saytini](https://korea-visa-production.up.railway.app) Telegram ichida **Web App** sifatida ochadigan tugma beradi. Chat pastidagi menyu tugmasi ham saytni ochadi, lekin u ham faqat obuna tasdiqlangan foydalanuvchida paydo bo'ladi.

- Faqat Python standart kutubxonasi ishlatiladi, `pip install` shart emas.
- Python 3.10+.

## Buyruqlar

| Buyruq | Vazifasi |
|---|---|
| `/start` | Salomlashish va sayt haqida ma'lumot. Obuna bo'lsa «🔎 Viza holatini tekshirish» tugmasi, bo'lmasa «📢 Kanalga obuna bo'lish» va «✅ Obuna bo'ldim» tugmalari |
| `/help` | Qanday foydalanish bo'yicha qisqa yo'riqnoma (obuna tekshiruvi bilan) |
| boshqa har qanday xabar | Tekshirish tugmasini qayta yuboradi (obuna tekshiruvi bilan) |

Bot buyruqlar ro'yxati va tavsifini ishga tushganda o'zi sozlaydi. Guruhlarda javob bermaydi, faqat shaxsiy chatda ishlaydi.

## Kanalga obuna majburiyati

- Obuna har safar `getChatMember` orqali tekshiriladi. Foydalanuvchi kanaldan chiqib ketsa, keyingi `/start` da Web App tugmasi va menyu yana yopiladi.
- **Botni kanalga administrator qilib qo'shing.** Hech qanday huquq belgilash shart emas, faqat admin bo'lsin. Busiz Telegram a'zolar ro'yxatini bermaydi, bot esa foydalanuvchiga "Obunani tekshirib bo'lmadi" deydi. Ishga tushganda loglarda `Kanal: @... (bot administrator)` qatori chiqishi kerak.
- Bu cheklov **bot ichida** ishlaydi. Sayt manzilini bilgan odam uni brauzerda to'g'ridan-to'g'ri ocha oladi.

## Railway'ga joylash

1. Railway'da **New → GitHub Repo** orqali `UtkirovMu/visabot` ni tanlang.
2. **Variables** bo'limiga `BOT_TOKEN` (@BotFather bergan token) va `CHANNEL_ID` (masalan `@turanschoolnews`) qo'shing.
3. Botni kanalga **administrator** qilib qo'shing.
4. Deploy qiling. Loglarda `Bot ishga tushdi: @...` yozuvi chiqishi kerak.

Build Dockerfile orqali bo'ladi (`railway.json`), shuning uchun Railpack kerak emas.

Bot long polling bilan ishlaydi, shuning uchun port yoki domen kerak emas. Bir vaqtda faqat **bitta** nusxa ishlashi kerak. Aks holda loglarda "getUpdates conflict" xatosi chiqadi.

### Ixtiyoriy o'zgaruvchilar

| Nomi | Standart |
|---|---|
| `CHANNEL_ID` | `@turanschoolnews`. Kanal `@username` yoki `-100...` raqamli ID |
| `CHANNEL_URL` | `CHANNEL_ID` dan olinadi. Yopiq kanal bo'lsa, taklif havolasini (`https://t.me/+...`) shu yerga yozing |
| `WEBAPP_URL` | `https://korea-visa-production.up.railway.app` |
| `LOG_LEVEL` | `INFO` |

O'z domeningizni ulasangiz, `WEBAPP_URL` ni yangilang va botni qayta ishga tushiring. Web App manzili albatta `https://` bilan boshlanishi kerak.

## Kompyuterda ishga tushirish

```bash
export BOT_TOKEN="..."
python bot.py
```

## Xavfsizlik

- Token kodda yoki repoda **saqlanmaydi**, faqat muhit o'zgaruvchisidan o'qiladi. `.env` fayllari `.gitignore` da.
- Xato loglarida token bor URL yozilmaydi.
- Foydalanuvchi ismi HTML-escape qilinadi (HTML injection yo'q).
- Tashqi paketlar yo'q, demak paketlar orqali keladigan xavf (supply chain) ham yo'q.
- Token tasodifan oshkor bo'lsa: @BotFather → `/revoke`, yangi tokenni Railway'ga qo'ying.
