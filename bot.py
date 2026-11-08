"""
Turan Int. School — Viza holatini tekshirish boti (Telegram Web App).

Foydalanuvchi kanalga obuna bo'lgandan keyingina Web App (tekshirish sahifasi) beriladi.
Faqat Python standart kutubxonasi ishlatiladi (tashqi paketlar yo'q).
Ishga tushirish:  BOT_TOKEN=... python bot.py
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import html
import json
import logging
import os
import signal
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

# --------------------------------------------------------------------------- #
#  Sozlamalar (faqat muhit o'zgaruvchilaridan — token kodda saqlanmaydi)
# --------------------------------------------------------------------------- #

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
WEBAPP_URL = os.environ.get("WEBAPP_URL", "https://korea-visa-production.up.railway.app").strip().rstrip("/")
CHANNEL_ID = os.environ.get("CHANNEL_ID", "@turanschoolnews").strip()  # @username yoki -100... ID
CHANNEL_URL = os.environ.get("CHANNEL_URL", "").strip() or (
    f"https://t.me/{CHANNEL_ID.lstrip('@')}" if CHANNEL_ID.startswith("@") else ""
)
API_BASE = os.environ.get("TELEGRAM_API_BASE", "https://api.telegram.org").rstrip("/")  # faqat test uchun o'zgaradi
POLL_TIMEOUT = 50  # soniya (long polling)
CHECK_SUB = "check_sub"  # "Obuna bo'ldim" tugmasi callback'i


def webapp_url_for(chat_id: int) -> str:
    """Web App manzili + imzolangan chat ID. Sayt imzoni tekshirib, natijani shu chatga yuboradi.

    imzo = base64url(HMAC_SHA256(key, chat_id)), key = HMAC_SHA256("turan-visa-link", BOT_TOKEN).
    Imzosiz yoki boshqa chat ID bilan sayt hech narsa yubormaydi.
    """
    key = hmac.new(b"turan-visa-link", BOT_TOKEN.encode(), hashlib.sha256).digest()
    sig = base64.urlsafe_b64encode(hmac.new(key, str(chat_id).encode(), hashlib.sha256).digest()).rstrip(b"=").decode()
    sep = "&" if "?" in WEBAPP_URL else "?"
    return f"{WEBAPP_URL}{sep}{urllib.parse.urlencode({'cid': chat_id, 'sig': sig})}"

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger("visabot")


# --------------------------------------------------------------------------- #
#  Matnlar
# --------------------------------------------------------------------------- #

def _name(first_name: str) -> str:
    return html.escape(first_name.strip()[:64]) or "do'st"


def start_text(first_name: str) -> str:
    return (
        f"Assalomu alaykum, <b>{_name(first_name)}</b>! 👋\n\n"
        "Bu bot <b>Turan Int. School</b> tomonidan talabalar uchun qulaylik yaratish "
        "maqsadida ishlab chiqilgan.\n\n"
        "🇰🇷 Bu yerda <b>Koreya vizasi</b> arizangiz holatini tekshirishingiz mumkin.\n\n"
        "<b>Kerakli ma'lumotlar:</b>\n"
        "• Pasport raqami\n"
        "• Familiya, ism, otasining ismi (pasportdagidek, lotin harflarida)\n"
        "• Tug'ilgan sana\n\n"
        "👇 Tekshirish uchun quyidagi tugmani bosing."
    )


def subscribe_text(first_name: str) -> str:
    return (
        f"Assalomu alaykum, <b>{_name(first_name)}</b>! 👋\n\n"
        "Bu bot <b>Turan Int. School</b> tomonidan talabalar uchun qulaylik yaratish "
        "maqsadida ishlab chiqilgan. Bu yerda <b>Koreya vizasi</b> arizangiz holatini "
        "tekshirishingiz mumkin.\n\n"
        "📢 Botdan foydalanish uchun avval <b>kanalimizga obuna bo'ling</b>, so'ng "
        "«✅ Obuna bo'ldim» tugmasini bosing."
    )


SUBSCRIBED_TEXT = (
    "✅ <b>Rahmat, obuna tasdiqlandi!</b>\n\n"
    "Endi viza holatingizni tekshirishingiz mumkin. Pasport raqami, F.I.Sh "
    "(pasportdagidek, lotin harflarida) va tug'ilgan sanangizni tayyorlab qo'ying.\n\n"
    "👇 Quyidagi tugmani bosing."
)

NOT_SUBSCRIBED_ALERT = "Siz hali kanalga obuna bo'lmagansiz. Avval obuna bo'ling, so'ng qayta bosing."
CHECK_FAILED_TEXT = "⚠️ Obunani tekshirib bo'lmadi. Birozdan so'ng qaytadan urinib ko'ring."

HELP_TEXT = (
    "ℹ️ <b>Qanday foydalaniladi?</b>\n\n"
    "1. Kanalimizga obuna bo'ling.\n"
    "2. «🔎 Viza holatini tekshirish» tugmasini bosing.\n"
    "3. Pasport ma'lumotlaringizni pasportdagidek lotin harflarida kiriting.\n"
    "4. «Tekshirish» tugmasini bosing — natija bir necha soniyada chiqadi.\n\n"
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


# --------------------------------------------------------------------------- #
#  Tugmalar
# --------------------------------------------------------------------------- #

def webapp_keyboard(chat_id: int) -> dict[str, Any]:
    # Sayt manzili ko'rsatilmaydi: faqat Telegram ichida ochiladigan Web App tugmasi
    rows: list[list[dict[str, Any]]] = [[{"text": "🔎 Viza holatini tekshirish", "web_app": {"url": webapp_url_for(chat_id)}}]]
    if CHANNEL_URL:
        rows.append([{"text": "📢 Kanalimiz", "url": CHANNEL_URL}])
    return {"inline_keyboard": rows}


def subscribe_keyboard() -> dict[str, Any]:
    rows: list[list[dict[str, Any]]] = []
    if CHANNEL_URL:
        rows.append([{"text": "📢 Kanalga obuna bo'lish", "url": CHANNEL_URL}])
    rows.append([{"text": "✅ Obuna bo'ldim", "callback_data": CHECK_SUB}])
    return {"inline_keyboard": rows}


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


def safe_api(method: str, payload: dict[str, Any]) -> Any:
    """Xato bo'lsa logga yozadi, botni to'xtatmaydi. 429 bo'lsa bir marta qayta urinadi."""
    try:
        return api(method, payload)
    except TelegramError as e:
        if e.retry_after:
            time.sleep(min(int(e.retry_after), 30))
            try:
                return api(method, payload)
            except TelegramError as e2:
                e = e2
        log.warning("%s xatosi: %s", method, e)  # masalan, foydalanuvchi botni bloklagan
        return None


def send(chat_id: int, text: str, keyboard: dict[str, Any] | None) -> None:
    payload: dict[str, Any] = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "link_preview_options": {"is_disabled": True},
    }
    if keyboard:
        payload["reply_markup"] = keyboard
    safe_api("sendMessage", payload)


# --------------------------------------------------------------------------- #
#  Kanalga obunani tekshirish
# --------------------------------------------------------------------------- #

MEMBER_STATUSES = {"creator", "administrator", "member"}


def is_subscribed(user_id: int) -> bool | None:
    """True — obuna, False — obuna emas, None — tekshirib bo'lmadi (bot kanalda admin emas va h.k.)."""
    try:
        m = api("getChatMember", {"chat_id": CHANNEL_ID, "user_id": user_id})
    except TelegramError as e:
        if "user not found" in str(e).lower() or "participant_id_invalid" in str(e).lower():
            return False
        log.error("getChatMember xatosi (%s): %s — bot kanalda administrator ekanini tekshiring.", CHANNEL_ID, e)
        return None
    status = (m or {}).get("status")
    if status in MEMBER_STATUSES:
        return True
    if status == "restricted":
        return bool((m or {}).get("is_member"))
    return False  # left, kicked


def set_user_menu(chat_id: int, subscribed: bool) -> None:
    """Pastdagi menyu tugmasi: obunachiga — Web App, boshqalarga — oddiy buyruqlar menyusi."""
    menu = (
        {"type": "web_app", "text": "Tekshirish", "web_app": {"url": webapp_url_for(chat_id)}}
        if subscribed else {"type": "commands"}
    )
    safe_api("setChatMenuButton", {"chat_id": chat_id, "menu_button": menu})


# --------------------------------------------------------------------------- #
#  Xabarlarni qayta ishlash
# --------------------------------------------------------------------------- #

def gate(chat_id: int, user_id: int, first_name: str, granted_text: str) -> None:
    """Obuna bo'lsa — Web App tugmasi, aks holda — obuna bo'lish taklifi."""
    sub = is_subscribed(user_id)
    if sub is None:
        send(chat_id, CHECK_FAILED_TEXT, None)
        return
    set_user_menu(chat_id, sub)
    if sub:
        send(chat_id, granted_text, webapp_keyboard(chat_id))
    else:
        send(chat_id, subscribe_text(first_name), subscribe_keyboard())


def custom_emoji_reply(msg: dict[str, Any]) -> str | None:
    """Xabarda premium (custom) emoji bo'lsa — ularning ID'larini qaytaradi (saytdagi TELEGRAM_CUSTOM_EMOJI uchun)."""
    text = msg.get("text") if isinstance(msg.get("text"), str) else ""
    ents = [e for e in (msg.get("entities") or []) if isinstance(e, dict) and e.get("type") == "custom_emoji"]
    if not ents:
        return None
    utf16 = text.encode("utf-16-le")
    lines, seen = [], set()
    for e in ents[:30]:
        eid = str(e.get("custom_emoji_id", ""))
        if not eid.isdigit() or eid in seen:
            continue
        seen.add(eid)
        off, ln = int(e.get("offset", 0)), int(e.get("length", 0))
        ch = utf16[off * 2:(off + ln) * 2].decode("utf-16-le", errors="ignore")
        lines.append(f'{html.escape(ch) or "⭐"}  <code>{eid}</code>')
    if not lines:
        return None
    return (
        "🆔 <b>Premium emoji ID'lari:</b>\n\n" + "\n".join(lines) + "\n\n"
        "Saytdagi <code>TELEGRAM_CUSTOM_EMOJI</code> o'zgaruvchisiga shunday yozing:\n"
        "<code>bell=ID,user=ID,status=ID,date=ID,type=ID,embassy=ID,time=ID,warn=ID,notfound=ID</code>"
    )


def handle_message(msg: dict[str, Any]) -> None:
    chat = msg.get("chat") or {}
    if chat.get("type") != "private":  # faqat shaxsiy chatlarda javob beradi
        return
    chat_id = chat.get("id")
    user = msg.get("from") or {}
    user_id = user.get("id")
    if not isinstance(chat_id, int) or not isinstance(user_id, int):
        return

    text = msg.get("text") if isinstance(msg.get("text"), str) else ""
    command = text.split()[0].split("@")[0].lower() if text.startswith("/") else ""
    first_name = str(user.get("first_name") or "")

    emoji_ids = custom_emoji_reply(msg)
    if emoji_ids:
        send(chat_id, emoji_ids, None)
        return

    if command == "/start":
        gate(chat_id, user_id, first_name, start_text(first_name))
    elif command == "/help":
        gate(chat_id, user_id, first_name, HELP_TEXT)
    else:
        gate(chat_id, user_id, first_name, FALLBACK_TEXT)


def handle_callback(cq: dict[str, Any]) -> None:
    cq_id = cq.get("id")
    user = cq.get("from") or {}
    user_id = user.get("id")
    msg = cq.get("message") or {}
    chat = msg.get("chat") or {}
    if not cq_id or not isinstance(user_id, int):
        return
    if cq.get("data") != CHECK_SUB or chat.get("type") != "private":
        safe_api("answerCallbackQuery", {"callback_query_id": cq_id})
        return

    sub = is_subscribed(user_id)
    if sub is None:
        safe_api("answerCallbackQuery", {"callback_query_id": cq_id, "text": CHECK_FAILED_TEXT, "show_alert": True})
        return
    if not sub:
        safe_api("answerCallbackQuery", {"callback_query_id": cq_id, "text": NOT_SUBSCRIBED_ALERT, "show_alert": True})
        return

    safe_api("answerCallbackQuery", {"callback_query_id": cq_id, "text": "✅ Obuna tasdiqlandi"})
    chat_id = chat.get("id")
    set_user_menu(chat_id, True)
    edited = safe_api("editMessageText", {
        "chat_id": chat_id,
        "message_id": msg.get("message_id"),
        "text": SUBSCRIBED_TEXT,
        "parse_mode": "HTML",
        "link_preview_options": {"is_disabled": True},
        "reply_markup": webapp_keyboard(chat_id),
    })
    if edited is None:  # xabar juda eski bo'lsa tahrirlab bo'lmaydi — yangisini yuboramiz
        send(chat_id, SUBSCRIBED_TEXT, webapp_keyboard(chat_id))


def handle_update(update: dict[str, Any]) -> None:
    if isinstance(update.get("message"), dict):
        handle_message(update["message"])
    elif isinstance(update.get("callback_query"), dict):
        handle_callback(update["callback_query"])


def setup_bot(bot_id: int) -> None:
    """Buyruqlar, umumiy menyu va tavsifni sozlash (har ishga tushganda)."""
    steps = [
        ("setMyCommands", {"commands": [
            {"command": "start", "description": "Botni ishga tushirish"},
            {"command": "help", "description": "Qanday foydalaniladi"},
        ]}),
        # Umumiy menyu — oddiy buyruqlar; Web App menyusi faqat obuna tasdiqlangan chatlarga qo'yiladi
        ("setChatMenuButton", {"menu_button": {"type": "commands"}}),
        ("setMyDescription", {"description": DESCRIPTION}),
        ("setMyShortDescription", {"short_description": SHORT_DESCRIPTION}),
    ]
    for method, payload in steps:
        try:
            api(method, payload)
        except TelegramError as e:
            log.warning("%s bajarilmadi: %s", method, e)

    # Bot kanalda administrator bo'lmasa, obunani tekshira olmaydi
    try:
        me_in_channel = api("getChatMember", {"chat_id": CHANNEL_ID, "user_id": bot_id})
        if me_in_channel.get("status") not in ("administrator", "creator"):
            log.error("Bot %s kanalida administrator emas — obunani tekshirib bo'lmaydi!", CHANNEL_ID)
        else:
            log.info("Kanal: %s (bot administrator)", CHANNEL_ID)
    except TelegramError as e:
        log.error("Kanalni tekshirib bo'lmadi (%s): %s — CHANNEL_ID to'g'riligini va bot admin ekanini tekshiring.", CHANNEL_ID, e)


# --------------------------------------------------------------------------- #
#  Asosiy sikl (long polling)
# --------------------------------------------------------------------------- #

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
    if not CHANNEL_ID:
        log.error("CHANNEL_ID o'rnatilmagan (masalan: @turanschoolnews).")
        sys.exit(1)
    if not CHANNEL_URL:
        log.warning("CHANNEL_URL yo'q — yopiq kanal bo'lsa, taklif havolasini CHANNEL_URL ga qo'ying.")

    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)

    me = api("getMe")
    log.info("Bot ishga tushdi: @%s", me.get("username"))
    api("deleteWebhook", {"drop_pending_updates": True})  # eski navbatdagi xabarlar tashlanadi
    setup_bot(int(me["id"]))

    offset = 0
    backoff = 1
    while True:
        try:
            updates = api(
                "getUpdates",
                {"offset": offset, "timeout": POLL_TIMEOUT, "allowed_updates": ["message", "callback_query"]},
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


if __name__ == "__main__":
    run()
