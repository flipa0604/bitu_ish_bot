"""Eski arizalarning ovozli xabari va videosini tiklab, Google Sheets'ga yozadi.

Eski kod ovoz/videoni saqlamagan (faqat vaqtinchalik havola yasab, adminga
matn qilib yuborgan). Lekin fayllarning o'zi Telegram serverida — nomzod bilan
bot orasidagi chatda turibdi.

Bot API chat tarixini o'qiy olmaydi, shuning uchun bu skript har bir nomzod
chatidagi xabarlarni ID bo'yicha `forwardMessage` qilib ko'radi: forward
qilingan xabardan `file_id` olinadi va nusxa darhol o'chiriladi. Nomzodlarga
hech qanday bildirishnoma bormaydi.

Ishlatish:
    venv/bin/python scripts/recover_media.py --target <ADMIN_CHAT_ID>
    venv/bin/python scripts/recover_media.py --target <ADMIN_CHAT_ID> --limit 2 --dry-run
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from aiogram import Bot
from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramRetryAfter,
)
from gspread.utils import rowcol_to_a1

from data.config import BOT_TOKEN, SHEET_TAB_NAME
from data.database import VOICE_HEADER, VIDEO_HEADER, get_all_applications, get_worksheet

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("recover")

MAX_MESSAGE_ID = 200          # bitta chatda tekshiriladigan eng katta xabar ID si
MAX_MISSES_IN_A_ROW = 15      # ketma-ket shuncha xabar topilmasa, chat tugagan deb hisoblanadi
REQUEST_DELAY = 0.08          # so'rovlar orasidagi tanaffus (~12 so'rov/sekund)
FLUSH_EVERY = 5               # nechta arizadan keyin Sheets'ga yozib qo'yish


async def _sleep():
    await asyncio.sleep(REQUEST_DELAY)


async def scan_chat(bot: Bot, target_chat_id: int, user_id: int, debug: bool = False):
    """Nomzod chatidan oxirgi ovozli xabar va videoning file_id sini topadi."""
    voice_file_id = None
    video_file_id = None
    hits = 0
    misses_in_a_row = 0
    seen_errors = set()

    for message_id in range(1, MAX_MESSAGE_ID + 1):
        try:
            message = await bot.forward_message(
                chat_id=target_chat_id,
                from_chat_id=user_id,
                message_id=message_id,
                disable_notification=True,
            )
        except TelegramRetryAfter as error:
            await asyncio.sleep(error.retry_after + 1)
            continue
        except TelegramForbiddenError:
            return voice_file_id, video_file_id, "bot bloklangan"
        except TelegramBadRequest as error:
            text = str(error).lower()
            if debug and text not in seen_errors:
                seen_errors.add(text)
                logger.info(f"      [debug] id={message_id}: {str(error)[:110]}")
            if "chat not found" in text:
                return voice_file_id, video_file_id, "chat topilmadi"
            misses_in_a_row += 1
            if hits and misses_in_a_row >= MAX_MISSES_IN_A_ROW:
                break
            if not hits and misses_in_a_row >= MAX_MISSES_IN_A_ROW:
                return voice_file_id, video_file_id, "xabarlar topilmadi"
            await _sleep()
            continue
        except Exception as error:  # kutilmagan xato — shu nomzodni tashlab ketamiz
            return voice_file_id, video_file_id, f"xato: {error}"

        hits += 1
        misses_in_a_row = 0

        # Eng oxirgi yuborilgani to'g'ri javob hisoblanadi (nomzod qayta yuborgan bo'lishi mumkin)
        if message.voice:
            voice_file_id = message.voice.file_id
        elif message.video_note:
            video_file_id = message.video_note.file_id
        elif message.video:
            video_file_id = message.video.file_id

        try:
            await bot.delete_message(chat_id=target_chat_id, message_id=message.message_id)
        except Exception:
            pass
        await _sleep()

    return voice_file_id, video_file_id, "ok"


def flush_to_sheet(worksheet, voice_col: int, video_col: int, updates: list, dry_run: bool):
    """Yig'ilgan file_id larni bitta so'rovda Sheets'ga yozadi."""
    if not updates or dry_run:
        updates.clear()
        return

    payload = []
    for row, voice_file_id, video_file_id in updates:
        if voice_file_id:
            payload.append({"range": rowcol_to_a1(row, voice_col), "values": [[voice_file_id]]})
        if video_file_id:
            payload.append({"range": rowcol_to_a1(row, video_col), "values": [[video_file_id]]})
    if payload:
        worksheet.batch_update(payload)
    updates.clear()


async def probe(bot: Bot, target_chat_id: int, source_chat_id: int):
    """Chatdagi xabar ID lari qaysi oraliqda ekanini aniqlaydi."""
    logger.info(f"Probe: manba {source_chat_id} -> nishon {target_chat_id}")

    # 1) Chatdagi joriy hisoblagichni bilish uchun ovozsiz xabar yuborib, darhol o'chiramiz
    marker = await bot.send_message(source_chat_id, ".", disable_notification=True)
    current_id = marker.message_id
    await bot.delete_message(source_chat_id, current_id)
    logger.info(f"  joriy message_id: {current_id}")

    # 2) Shu ID atrofidagi xabarlarni forward qilib ko'ramiz
    candidates = [current_id - offset for offset in (1, 2, 3, 5, 10, 20, 40, 80, 160)]
    candidates = [c for c in candidates if c > 0]
    for message_id in candidates:
        try:
            message = await bot.forward_message(
                chat_id=target_chat_id,
                from_chat_id=source_chat_id,
                message_id=message_id,
                disable_notification=True,
            )
            logger.info(f"  id={message_id}: OK -> {message.content_type}")
            try:
                await bot.delete_message(target_chat_id, message.message_id)
            except Exception as error:
                logger.info(f"      nusxa o'chirilmadi: {str(error)[:60]}")
        except Exception as error:
            logger.info(f"  id={message_id}: {type(error).__name__} {str(error)[:80]}")
        await _sleep()


async def scan_back(bot: Bot, target_chat_id: int, source_chat_id: int, window: int):
    """Chatning oxirgi xabaridan orqaga qarab ovoz/video izlaydi va statistika beradi."""
    marker = await bot.send_message(source_chat_id, ".", disable_notification=True)
    anchor = marker.message_id
    await bot.delete_message(source_chat_id, anchor)
    logger.info(f"anchor={anchor}, {window} ta ID orqaga tekshiriladi")

    hits = 0
    types = {}
    voice_at = video_at = None
    for step in range(1, window + 1):
        message_id = anchor - step
        if message_id <= 0:
            break
        try:
            message = await bot.forward_message(
                chat_id=target_chat_id,
                from_chat_id=source_chat_id,
                message_id=message_id,
                disable_notification=True,
            )
        except TelegramRetryAfter as error:
            await asyncio.sleep(error.retry_after + 1)
            continue
        except Exception as error:
            text = str(error)
            if "VOICE_MESSAGES_FORBIDDEN" in text:
                # Xabar bor, lekin nishon chat ovozli xabarlarni qabul qilmaydi
                logger.info(f"  OVOZ bor, lekin bloklangan: anchor-{step} (id={message_id})")
                if voice_at is None:
                    voice_at = step
            elif "message to forward not found" not in text.lower():
                logger.info(f"  [xato] anchor-{step}: {text[:90]}")
            await _sleep()
            continue

        hits += 1
        types[message.content_type] = types.get(message.content_type, 0) + 1
        if message.voice and voice_at is None:
            voice_at = step
            logger.info(f"  OVOZ topildi: anchor-{step} (id={message_id})")
        if message.video_note and video_at is None:
            video_at = step
            logger.info(f"  VIDEO topildi: anchor-{step} (id={message_id})")

        try:
            await bot.delete_message(target_chat_id, message.message_id)
        except Exception:
            pass
        if voice_at and video_at:
            break
        await _sleep()

    logger.info(f"topilgan xabarlar: {hits} ta, turlari: {types}")
    logger.info(f"ovoz: {voice_at}, video: {video_at} (anchordan necha ID orqada)")


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=int, required=True, help="forward qilinadigan admin chat ID si")
    parser.add_argument("--limit", type=int, default=0, help="nechta arizani tekshirish (0 = hammasi)")
    parser.add_argument("--dry-run", action="store_true", help="Sheets'ga yozmasdan sinab ko'rish")
    parser.add_argument("--newest-first", action="store_true", help="oxirgi arizalardan boshlash")
    parser.add_argument("--debug", action="store_true", help="Telegram xatolarini ko'rsatish")
    parser.add_argument("--probe", type=int, default=0, help="shu chat ID sida xabar ID oralig'ini tekshirish")
    parser.add_argument("--window", type=int, default=0, help="probe bilan: oxirgi xabardan necha ID orqaga qidirish")
    args = parser.parse_args()

    if args.probe:
        bot = Bot(token=BOT_TOKEN)
        try:
            if args.window:
                await scan_back(bot, args.target, args.probe, args.window)
            else:
                await probe(bot, args.target, args.probe)
        finally:
            await bot.session.close()
        return

    worksheet = get_worksheet(SHEET_TAB_NAME)
    if not worksheet:
        logger.error("Sheet topilmadi")
        return

    headers = worksheet.row_values(1)
    voice_col = headers.index(VOICE_HEADER) + 1
    video_col = headers.index(VIDEO_HEADER) + 1

    applications = get_all_applications()
    if args.newest_first:
        applications = list(reversed(applications))

    todo = [
        app for app in applications
        if str(app.get("TelegramID", "")).strip().isdigit()
        and not ((app.get(VOICE_HEADER) or "").strip() and (app.get(VIDEO_HEADER) or "").strip())
    ]
    if args.limit:
        todo = todo[:args.limit]

    logger.info(f"Tekshiriladi: {len(todo)} ta ariza (jami {len(applications)})")

    bot = Bot(token=BOT_TOKEN)
    updates = []
    stats = {"voice": 0, "video": 0, "both": 0, "none": 0}

    try:
        for number, app in enumerate(todo, start=1):
            user_id = int(str(app["TelegramID"]).strip())
            name = (app.get("Ism Familya") or "?")[:25]

            voice_file_id, video_file_id, status = await scan_chat(
                bot, args.target, user_id, debug=args.debug
            )

            if voice_file_id:
                stats["voice"] += 1
            if video_file_id:
                stats["video"] += 1
            if voice_file_id and video_file_id:
                stats["both"] += 1
            if not voice_file_id and not video_file_id:
                stats["none"] += 1

            logger.info(
                f"{number}/{len(todo)} {name:<25} ovoz:{'✔' if voice_file_id else '—'} "
                f"video:{'✔' if video_file_id else '—'} ({status})"
            )

            if voice_file_id or video_file_id:
                updates.append((app["_row"], voice_file_id, video_file_id))
            if len(updates) >= FLUSH_EVERY:
                flush_to_sheet(worksheet, voice_col, video_col, updates, args.dry_run)

        flush_to_sheet(worksheet, voice_col, video_col, updates, args.dry_run)
    finally:
        await bot.session.close()

    logger.info(
        f"\nNatija: ovoz {stats['voice']} ta, video {stats['video']} ta, "
        f"ikkalasi {stats['both']} ta, hech nima topilmadi {stats['none']} ta"
        + (" (dry-run: Sheets'ga yozilmadi)" if args.dry_run else "")
    )


if __name__ == "__main__":
    asyncio.run(main())
