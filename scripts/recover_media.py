"""Eski arizalarning ovozli xabari va videosini tiklab, Google Sheets'ga yozadi.

Eski kod ovoz/videoni saqlamagan (faqat vaqtinchalik havola yasab, adminga matn
qilib yuborgan). Lekin fayllarning o'zi Telegram serverida — nomzod bilan bot
orasidagi chatda turibdi.

Bot API chat tarixini o'qiy olmaydi. Shuning uchun:
  1) nomzod chatiga ovozsiz "." xabar yuboriladi va darhol o'chiriladi — bu
     chatdagi joriy message_id ni bilish uchun kerak (Telegram'da shaxsiy chat
     ID lari 1 dan emas, akkaunt hisoblagichidan boradi);
  2) o'sha ID dan orqaga qarab xabarlar `forwardMessage` bilan tekshiriladi —
     forward qilingan xabardan `file_id` olinadi, nusxa darhol o'chiriladi;
  3) topilgan file_id lar Sheets'ga yoziladi.

Nomzodlarga bildirishnoma bormaydi (forward manba chatda ko'rinmaydi, "." esa
ovozsiz yuborilib darhol o'chiriladi).

Ishlatish:
    venv/bin/python scripts/recover_media.py --target <ADMIN_CHAT_ID>
    venv/bin/python scripts/recover_media.py --target <ID> --limit 3 --dry-run
    venv/bin/python scripts/recover_media.py --target <ID> --probe <CHAT_ID>
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter
from gspread.utils import rowcol_to_a1

from data.config import BOT_TOKEN, SHEET_TAB_NAME
from data.database import VOICE_HEADER, VIDEO_HEADER, get_all_applications, get_worksheet

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("recover")

DEFAULT_WINDOW = 2000    # bitta chatda orqaga tekshiriladigan ID lar soni
DEFAULT_MISS_LIMIT = 400  # oxirgi topilgan xabardan keyin shuncha bo'sh ID bo'lsa, to'xtaymiz
DEFAULT_DELAY = 0.05      # so'rovlar orasidagi tanaffus (~20 so'rov/sekund)
FLUSH_EVERY = 5           # nechta arizadan keyin Sheets'ga yozib qo'yish


class Scanner:
    def __init__(self, bot: Bot, target_chat_id: int, window: int, miss_limit: int, delay: float):
        self.bot = bot
        self.target = target_chat_id
        self.window = window
        self.miss_limit = miss_limit
        self.delay = delay

    async def _pause(self):
        await asyncio.sleep(self.delay)

    async def _anchor(self, user_id: int):
        """Chatdagi joriy message_id ni aniqlaydi (ovozsiz xabar yuborib, o'chiradi)."""
        marker = await self.bot.send_message(user_id, ".", disable_notification=True)
        try:
            await self.bot.delete_message(user_id, marker.message_id)
        except Exception:
            pass
        return marker.message_id

    async def scan(self, user_id: int):
        """Chatdan oxirgi ovozli xabar va videoning file_id sini qaytaradi."""
        try:
            anchor = await self._anchor(user_id)
        except TelegramForbiddenError:
            return None, None, "bot bloklangan"
        except Exception as error:
            return None, None, f"chat ochilmadi ({str(error)[:40]})"

        voice_file_id = None
        video_file_id = None
        voice_blocked = False
        hits = 0
        misses = 0

        for step in range(1, self.window + 1):
            message_id = anchor - step
            if message_id <= 0:
                break

            try:
                message = await self.bot.forward_message(
                    chat_id=self.target,
                    from_chat_id=user_id,
                    message_id=message_id,
                    disable_notification=True,
                )
            except TelegramRetryAfter as error:
                await asyncio.sleep(error.retry_after + 1)
                continue
            except TelegramForbiddenError:
                return voice_file_id, video_file_id, "bot bloklangan"
            except Exception as error:
                if "VOICE_MESSAGES_FORBIDDEN" in str(error):
                    # Xabar bor, lekin nishon chat ovozli xabarni qabul qilmaydi
                    voice_blocked = True
                misses += 1
                if hits and misses >= self.miss_limit:
                    break
                await self._pause()
                continue

            hits += 1
            misses = 0

            # Eng oxirgisi to'g'ri javob (nomzod qayta yuborgan bo'lishi mumkin)
            if message.voice and not voice_file_id:
                voice_file_id = message.voice.file_id
            elif message.video_note and not video_file_id:
                video_file_id = message.video_note.file_id
            elif message.video and not video_file_id:
                video_file_id = message.video.file_id

            try:
                await self.bot.delete_message(self.target, message.message_id)
            except Exception:
                pass

            if voice_file_id and video_file_id:
                return voice_file_id, video_file_id, f"topildi ({hits} xabar)"
            await self._pause()

        if voice_blocked and not voice_file_id:
            return voice_file_id, video_file_id, "ovoz bloklangan (adminda cheklov)"
        if not hits:
            return None, None, "chat xabarlari topilmadi"
        return voice_file_id, video_file_id, f"qisman ({hits} xabar)"


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


async def probe(bot: Bot, target_chat_id: int, source_chat_id: int, window: int, delay: float):
    """Bitta chatni tekshirib, natijani ko'rsatadi (sozlashni sinash uchun)."""
    scanner = Scanner(bot, target_chat_id, window, DEFAULT_MISS_LIMIT, delay)
    voice_file_id, video_file_id, status = await scanner.scan(source_chat_id)
    logger.info(f"ovoz: {'✔' if voice_file_id else '—'} video: {'✔' if video_file_id else '—'} ({status})")


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=int, required=True, help="forward qilinadigan admin chat ID si")
    parser.add_argument("--limit", type=int, default=0, help="nechta arizani tekshirish (0 = hammasi)")
    parser.add_argument("--dry-run", action="store_true", help="Sheets'ga yozmasdan sinash")
    parser.add_argument("--newest-first", action="store_true", help="oxirgi arizalardan boshlash")
    parser.add_argument("--probe", type=int, default=0, help="faqat shu chat ID sini tekshirish")
    parser.add_argument("--window", type=int, default=DEFAULT_WINDOW)
    parser.add_argument("--miss-limit", type=int, default=DEFAULT_MISS_LIMIT)
    parser.add_argument("--delay", type=float, default=DEFAULT_DELAY)
    args = parser.parse_args()

    if args.probe:
        bot = Bot(token=BOT_TOKEN)
        try:
            await probe(bot, args.target, args.probe, args.window, args.delay)
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

    logger.info(f"Tekshiriladi: {len(todo)} ta ariza (jami {len(applications)}), window={args.window}")

    bot = Bot(token=BOT_TOKEN)
    scanner = Scanner(bot, args.target, args.window, args.miss_limit, args.delay)
    updates = []
    stats = {"voice": 0, "video": 0, "both": 0, "none": 0}

    try:
        for number, app in enumerate(todo, start=1):
            user_id = int(str(app["TelegramID"]).strip())
            name = (app.get("Ism Familya") or "?")[:24]

            try:
                voice_file_id, video_file_id, status = await scanner.scan(user_id)
            except Exception as error:
                voice_file_id = video_file_id = None
                status = f"xato: {str(error)[:50]}"

            if voice_file_id:
                stats["voice"] += 1
            if video_file_id:
                stats["video"] += 1
            if voice_file_id and video_file_id:
                stats["both"] += 1
            if not voice_file_id and not video_file_id:
                stats["none"] += 1

            logger.info(
                f"{number}/{len(todo)} {name:<24} ovoz:{'✔' if voice_file_id else '—'} "
                f"video:{'✔' if video_file_id else '—'}  {status}"
            )

            if voice_file_id or video_file_id:
                updates.append((app["_row"], voice_file_id, video_file_id))
            if len(updates) >= FLUSH_EVERY:
                flush_to_sheet(worksheet, voice_col, video_col, updates, args.dry_run)

        flush_to_sheet(worksheet, voice_col, video_col, updates, args.dry_run)
    finally:
        await bot.session.close()

    logger.info(
        f"NATIJA: ovoz {stats['voice']} ta, video {stats['video']} ta, "
        f"ikkalasi {stats['both']} ta, topilmadi {stats['none']} ta"
        + (" (dry-run: Sheets'ga yozilmadi)" if args.dry_run else "")
    )


if __name__ == "__main__":
    asyncio.run(main())
