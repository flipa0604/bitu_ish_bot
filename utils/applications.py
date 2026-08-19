"""Arizalarni chiroyli matn ko'rinishida va media (ovoz/video) bilan yuborish uchun yordamchilar."""

import asyncio
import html
import logging

from aiogram import Bot
from aiogram.exceptions import TelegramRetryAfter

from data.database import VOICE_HEADER, VIDEO_HEADER

logger = logging.getLogger(__name__)

MAX_MESSAGE_LENGTH = 3900

# Sheet ustuni -> ko'rsatiladigan sarlavha
FIELD_LABELS = [
    ("Ism Familya", "👤 Ism"),
    ("Telefon", "📞 Telefon"),
    ("Manzil", "🏠 Manzil"),
    ("Tug'ilgan sana", "🎂 Tug'ilgan sana"),
    ("Ma'lumoti", "🎓 Ta'lim"),
    ("Ish tajriba", "💼 Ish tajriba"),
    ("Oilaviy Holat", "💍 Oilaviy holat"),
    ("Lavozimi", "🎯 Lavozim"),
    ("Ingliz tilini bilishi", "🇬🇧 Ingliz tili"),
    ("Rus tilini bilishi", "🇷🇺 Rus tili"),
    ("Kutayotgan maosh", "💰 Kutilayotgan maosh"),
    ("Aloqa ma'lumoti", "📋 Tavsiyachi"),
    ("Ish muddati", "⏰ Ish muddati"),
    ("Qo'shimcha ish", "🕐 Qo'shimcha ish"),
    ("Ish sabablari", "🎯 Ish sababi"),
    ("Sog'liq holati", "🏥 Sog'liq"),
    ("Kechikish sababi", "🐢 Kechikish sababi"),
    ("O'g'irlik sababi", "🚨 O'g'irlik sababi"),
    ("Ish sifati sababi", "⚖️ Ish sifati sababi"),
    ("Oldingi maosh", "💸 Oldingi maosh"),
    ("O'qigan kurslari", "📚 Kurslar"),
]


def escape_html(value) -> str:
    text = str(value).strip() if value is not None else ''
    return html.escape(text, quote=False) if text else '—'


def _is_link(value: str) -> bool:
    return isinstance(value, str) and value.strip().lower().startswith('http')


def format_application_text(app: dict, title: str = "📄 <b>Ariza</b>") -> str:
    """Sheetdan olingan bitta ariza (dict) ni matn ko'rinishiga o'tkazadi."""
    lines = [title, ""]
    for header, label in FIELD_LABELS:
        if header in app:
            lines.append(f"<b>{label}:</b> {escape_html(app.get(header))}")

    accepted = str(app.get("Qabul qilindi", '')).strip().upper()
    status = "✅ Qabul qilindi" if accepted in ("TRUE", "HA", "YES", "1") else "⏳ Ko'rib chiqilmoqda"
    lines.append("")
    lines.append(f"<b>📌 Holati:</b> {status}")

    telegram_id = str(app.get("TelegramID", '')).strip()
    if telegram_id:
        lines.append(f"<b>🆔 Telegram ID:</b> <code>{escape_html(telegram_id)}</code>")

    return "\n".join(lines)


def application_title(app: dict) -> str:
    """Ro'yxatdagi tugma uchun qisqa sarlavha."""
    name = (app.get("Ism Familya") or "Noma'lum").strip()
    position = (app.get("Lavozimi") or '').strip().replace('_', ' ')
    label = f"{name} — {position}" if position else name
    return label[:55]


async def _call(method, *args, **kwargs):
    """Telegram flood-limitiga tushsa, kutib qayta urinadi."""
    try:
        return await method(*args, **kwargs)
    except TelegramRetryAfter as error:
        await asyncio.sleep(error.retry_after + 1)
        return await method(*args, **kwargs)


async def send_long_message(bot: Bot, chat_id: int, text: str, **kwargs):
    """4096 belgidan uzun matnni bo'laklarga bo'lib yuboradi."""
    if len(text) <= MAX_MESSAGE_LENGTH:
        return await _call(bot.send_message, chat_id, text, **kwargs)

    chunk = ''
    for line in text.split("\n"):
        if len(chunk) + len(line) + 1 > MAX_MESSAGE_LENGTH:
            await _call(bot.send_message, chat_id, chunk)
            chunk = ''
        chunk += line + "\n"
    if chunk.strip():
        return await _call(bot.send_message, chat_id, chunk, **kwargs)


async def send_voice_file(bot: Bot, chat_id: int, voice: str, caption: str = "🎙 <b>Ovozli xabar</b> (qarindoshlari haqida)"):
    if _is_link(voice):
        # Eski arizalar: file_id o'rniga havola saqlangan
        await _call(bot.send_message, chat_id, f"{caption}\n{escape_html(voice)}")
        return
    await _call(bot.send_voice, chat_id, voice=voice, caption=caption)


async def send_video_file(bot: Bot, chat_id: int, video: str, caption: str = "📹 <b>Video xabar</b> (shaxsiy sifatlari)"):
    if _is_link(video):
        await _call(bot.send_message, chat_id, f"{caption}\n{escape_html(video)}")
        return
    # video_note (yumaloq video) caption'ni qo'llab-quvvatlamaydi
    await _call(bot.send_message, chat_id, caption)
    try:
        await _call(bot.send_video_note, chat_id, video_note=video)
    except Exception:
        await _call(bot.send_video, chat_id, video=video)


async def send_application_media(
    bot: Bot,
    chat_id: int,
    voice_file_id: str = None,
    video_file_id: str = None,
    note_if_missing: bool = True,
):
    """Arizaga biriktirilgan ovozli xabar va videoni yuboradi."""
    if voice_file_id:
        try:
            await send_voice_file(bot, chat_id, voice_file_id)
        except Exception as error:
            logger.error(f"Ovozli xabar yuborilmadi (chat {chat_id}): {error}")
            await _call(bot.send_message, chat_id, "🎙 Ovozli xabarni yuborib bo'lmadi.")
    elif note_if_missing:
        await _call(bot.send_message, chat_id, "🎙 Ovozli xabar saqlanmagan (eski ariza).")

    if video_file_id:
        try:
            await send_video_file(bot, chat_id, video_file_id)
        except Exception as error:
            logger.error(f"Video xabar yuborilmadi (chat {chat_id}): {error}")
            await _call(bot.send_message, chat_id, "📹 Video xabarni yuborib bo'lmadi.")
    elif note_if_missing:
        await _call(bot.send_message, chat_id, "📹 Video xabar saqlanmagan (eski ariza).")


async def send_full_application(bot: Bot, chat_id: int, app: dict, title: str = "📄 <b>Ariza</b>"):
    """Bitta arizani to'liq yuboradi: ma'lumotlari + ovozli xabari + videosi."""
    await send_long_message(bot, chat_id, format_application_text(app, title=title))
    await send_application_media(
        bot,
        chat_id,
        voice_file_id=(app.get(VOICE_HEADER) or '').strip() or None,
        video_file_id=(app.get(VIDEO_HEADER) or '').strip() or None,
    )
