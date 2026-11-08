# Turan Int. School — Viza holati boti

Telegram bot: `/start` bosilganda sayt haqida aytib beradi va [viza holatini tekshirish saytini](https://korea-visa-production.up.railway.app) Telegram ichida **Web App** sifatida ochadigan tugma beradi. Chat pastidagi menyu tugmasi ham saytni ochadi.

- Faqat Python standart kutubxonasi ishlatiladi, `pip install` shart emas.
- Python 3.10+.

## Buyruqlar

| Buyruq | Vazifasi |
|---|---|
| `/start` | Salomlashish, sayt haqida ma'lumot va «🔎 Viza holatini tekshirish» tugmasi |
| `/help` | Qanday foydalanish bo'yicha qisqa yo'riqnoma |
| boshqa har qanday xabar | Tekshirish tugmasini qayta yuboradi |

Bot ishga tushganda menyu tugmasi, buyruqlar ro'yxati va bot tavsifini o'zi sozlaydi. Guruhlarda javob bermaydi, faqat shaxsiy chatda ishlaydi.

## Railway'ga joylash

1. Railway'da **New → GitHub Repo** orqali `UtkirovMu/visabot` ni tanlang.
2. **Variables** bo'limiga `BOT_TOKEN` qo'shing (@BotFather bergan token).
3. Deploy qiling. Loglarda `Bot ishga tushdi: @...` yozuvi chiqishi kerak.

Bot long polling bilan ishlaydi, shuning uchun port yoki domen kerak emas. Bir vaqtda faqat **bitta** nusxa ishlashi kerak. Aks holda loglarda "getUpdates conflict" xatosi chiqadi.

### Ixtiyoriy o'zgaruvchilar

| Nomi | Standart |
|---|---|
| `WEBAPP_URL` | `https://korea-visa-production.up.railway.app` |
| `CHANNEL_URL` | `https://t.me/turanschoolnews` |
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
