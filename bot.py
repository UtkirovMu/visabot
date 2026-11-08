"""
Turan Int. School — Viza holatini tekshirish boti (Telegram Web App).

Faqat Python standart kutubxonasi ishlatiladi (tashqi paketlar yo'q).
Ishga tushirish:  BOT_TOKEN=... python bot.py
"""

from __future__ import annotations

import html
import json
import logging
import os
import signal
import sys
import time
import urllib.error
import urllib.request
from typing import Any

# --------------------------------------------------------------------------- #
#  Sozlamalar (faqat muhit o'zgaruvchilaridan — token kodda saqlanmaydi)
# --------------------------------------------------------------------------- #

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
WEBAPP_URL = os.environ.get("WEBAPP_URL", "https://korea-visa-production.up.railway.app").strip().rstrip("/")
CHANNEL_URL = os.environ.get("CHANNEL_URL", "https://t.me/turanschoolnews").strip()
API_BASE = os.environ.get("TELEGRAM_API_BASE", "https://api.telegram.org").rstrip("/")  # faqat test uchun o'zgaradi
POLL_TIMEOUT = 50  # soniya (long polling)

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger("visabot")


# --------------------------------------------------------------------------- #
#  Matnlar
# --------------------------------------------------------------------------- #

def start_text(first_name: str) -> str:
    name = html.escape(first_name.strip()[:64]) or "do'st"
    return (
        f"Assalomu alaykum, <b>{name}</b>! 👋\n\n"
        "Bu bot <b>Turan Int. School</b> tomonidan talabalar uchun qulaylik yaratish "
        "maqsadida ishlab chiqilgan.\n\n"
        "🇰🇷 Bu yerda <b>Koreya vizasi</b> arizangiz holatini tekshirishingiz mumkin.\n\n"
        "<b>Kerakli ma'lumotlar:</b>\n"
        "• Pasport raqami\n"
        "• Familiya, ism, otasining ismi (pasportdagidek, lotin harflarida)\n"
        "• Tug'ilgan sana\n\n"
        "👇 Tekshirish uchun quyidagi tugmani bosing."
    )


HELP_TEXT = (
    "ℹ️ <b>Qanday foydalaniladi?</b>\n\n"
    "1. «🔎 Viza holatini tekshirish» tugmasini bosing.\n"
    "2. Pasport ma'lumotlaringizni pasportdagidek lotin harflarida kiriting.\n"
    "3. «Tekshirish» tugmasini bosing — natija bir necha soniyada chiqadi.\n\n"
    "<i>Ma'lumotlaringiz saqlanmaydi — faqat tekshiruv uchun ishlatiladi.\n"
    "Ma'lumotlar rasmiy visa.go.kr saytidan olinadi.</i>"
)

FALLBACK_TEXT = "Viza holatini tekshirish uchun quyidagi tugmani bosing 👇"

DESCRIPTION = (
    "Turan Int. School — Koreya vizasi arizangiz holatini tekshirish boti.\n\n"
    "Pasport ma'lumotlaringizni kiriting va viza holatingizni bir necha soniyada bilib oling.\n\n"
    "Boshlash uchun «Start» tugmasini bosing."
)
SHORT_DESCRIPTION = "Koreya vizasi holatini tekshirish — Turan Int. School"


def main_keyboard() -> dict[str, Any]:
    return {
        "inline_keyboard": [
            [{"text": "🔎 Viza holatini tekshirish", "web_app": {"url": WEBAPP_URL}}],
            [
                {"text": "🌐 Brauzerda ochish", "url": WEBAPP_URL},
                {"text": "📢 Kanalimiz", "url": CHANNEL_URL},
            ],
        ]
    }


# --------------------------------------------------------------------------- #
#  Telegram Bot API
# --------------------------------------------------------------------------- #

class TelegramError(Exception):
    def __init__(self, description: str, retry_after: int | None = None):
        super().__init__(description)
        self.retry_after = retry_after


def api(method: str, payload: dict[str, Any] | None = None, timeout: float = 15) -> Any:
    url = f"{API_BASE}/bot{BOT_TOKEN}/{method}"
    data = json.dumps(payload or {}).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read().decode("utf-8"))
        except Exception:
            raise TelegramError(f"HTTP {e.code}") from None
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        # Xatoda URL (token bilan) log qilinmasligi uchun faqat sabab
        raise TelegramError(f"network: {type(e).__name__}") from None

    if not body.get("ok"):
        params = body.get("parameters") or {}
        raise TelegramError(str(body.get("description", "unknown error")), params.get("retry_after"))
    return body.get("result")


def send(chat_id: int, text: str, keyboard: bool = True) -> None:
    payload: dict[str, Any] = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "link_preview_options": {"is_disabled": True},
    }
    if keyboard:
        payload["reply_markup"] = main_keyboard()
    try:
        api("sendMessage", payload)
    except TelegramError as e:
        if e.retry_after:
            time.sleep(min(int(e.retry_after), 30))
            api("sendMessage", payload)
        else:
            # Masalan, foydalanuvchi botni bloklagan — xavfsiz e'tiborsiz qoldiriladi
            log.warning("sendMessage xatosi: %s", e)


# --------------------------------------------------------------------------- #
#  Xabarlarni qayta ishlash
# --------------------------------------------------------------------------- #

def handle_update(update: dict[str, Any]) -> None:
    msg = update.get("message")
    if not isinstance(msg, dict):
        return
    chat = msg.get("chat") or {}
    if chat.get("type") != "private":  # faqat shaxsiy chatlarda javob beradi
        return
    chat_id = chat.get("id")
    if not isinstance(chat_id, int):
        return

    text = msg.get("text") if isinstance(msg.get("text"), str) else ""
    command = text.split()[0].split("@")[0].lower() if text.startswith("/") else ""
    user = msg.get("from") or {}

    if command == "/start":
        send(chat_id, start_text(str(user.get("first_name") or "")))
    elif command == "/help":
        send(chat_id, HELP_TEXT)
    else:
        send(chat_id, FALLBACK_TEXT)


def setup_bot() -> None:
    """Bot menyusi, buyruqlar va tavsifni sozlash (har ishga tushganda)."""
    steps = [
        ("setMyCommands", {"commands": [
            {"command": "start", "description": "Botni ishga tushirish"},
            {"command": "help", "description": "Qanday foydalaniladi"},
        ]}),
        ("setChatMenuButton", {"menu_button": {
            "type": "web_app", "text": "Tekshirish", "web_app": {"url": WEBAPP_URL},
        }}),
        ("setMyDescription", {"description": DESCRIPTION}),
        ("setMyShortDescription", {"short_description": SHORT_DESCRIPTION}),
    ]
    for method, payload in steps:
        try:
            api(method, payload)
        except TelegramError as e:
            log.warning("%s bajarilmadi: %s", method, e)


# --------------------------------------------------------------------------- #
#  Asosiy sikl (long polling)
# --------------------------------------------------------------------------- #

running = True


def _stop(signum: int, _frame: Any) -> None:
    # Saqlanadigan holat yo'q — long polling'ni kutmasdan darhol chiqamiz
    log.info("To'xtatilmoqda (signal %s)…", signum)
    raise SystemExit(0)


def run() -> None:
    if not BOT_TOKEN or ":" not in BOT_TOKEN:
        log.error("BOT_TOKEN muhit o'zgaruvchisi o'rnatilmagan.")
        sys.exit(1)
    if not WEBAPP_URL.startswith("https://"):
        log.error("WEBAPP_URL https:// bilan boshlanishi shart (Telegram Web App talabi).")
        sys.exit(1)

    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)

    me = api("getMe")
    log.info("Bot ishga tushdi: @%s", me.get("username"))
    api("deleteWebhook", {"drop_pending_updates": True})  # eski navbatdagi xabarlar tashlanadi
    setup_bot()

    offset = 0
    backoff = 1
    while running:
        try:
            updates = api(
                "getUpdates",
                {"offset": offset, "timeout": POLL_TIMEOUT, "allowed_updates": ["message"]},
                timeout=POLL_TIMEOUT + 10,
            )
            backoff = 1
        except TelegramError as e:
            if "Conflict" in str(e):
                log.error("Boshqa joyda ham shu bot ishlayapti (getUpdates conflict). Faqat bitta nusxa ishlashi kerak.")
            else:
                log.warning("getUpdates xatosi: %s", e)
            time.sleep(e.retry_after or backoff)
            backoff = min(backoff * 2, 30)
            continue

        for update in updates or []:
            offset = max(offset, int(update.get("update_id", 0)) + 1)
            try:
                handle_update(update)
            except Exception:
                log.exception("Update'ni qayta ishlashda xato")

    log.info("Bot to'xtadi.")


if __name__ == "__main__":
    run()
