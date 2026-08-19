"""Bitta foydalanuvchining bot bilan yozishmalar tarixini chiqaradi.

Bot API chat tarixini o'qiy olmaydi va loglarda foydalanuvchi ID lari yozilmaydi.
Shuning uchun tarix `forwardMessage` orqali tiklanadi: chatdagi joriy message_id
aniqlanadi (ovozsiz "." xabar yuborib, darhol o'chiriladi), so'ng ID lar orqaga
qarab forward qilib ko'riladi. Forward qilingan nusxadan sana, muallif va matn
o'qiladi va nusxa darhol o'chiriladi.

Ishlatish:
    venv/bin/python scripts/chat_history.py --target <ADMIN_CHAT_ID> --chat <USER_ID>
    venv/bin/python scripts/chat_history.py --target <ID> --chat <ID> --window 1500 --delay 0.15
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter

from data.config import BOT_TOKEN

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("history")


def describe(message) -> tuple:
    """Forward qilingan xabardan (sana, muallif, tur, matn) ni ajratib oladi."""
    origin = message.forward_origin
    date = getattr(origin, "date", None)
    sender = getattr(origin, "sender_user", None)
    if sender is not None:
        author = f"bot" if sender.is_bot else f"user:{sender.id}"
    elif getattr(origin, "sender_user_name", None):
        author = origin.sender_user_name
    else:
        author = "?"

    text = message.text or message.caption or ""
    text = " ".join(text.split())
    return date, author, message.content_type, text


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=int, required=True, help="forward qilinadigan chat (o'qish uchun)")
    parser.add_argument("--chat", type=int, required=True, help="tarixi kerak bo'lgan foydalanuvchi ID si")
    parser.add_argument("--window", type=int, default=800)
    parser.add_argument("--delay", type=float, default=0.15)
    parser.add_argument("--only-user", action="store_true", help="faqat foydalanuvchi xabarlarini ko'rsatish")
    args = parser.parse_args()

    bot = Bot(token=BOT_TOKEN)
    found = []
    try:
        try:
            marker = await bot.send_message(args.chat, ".", disable_notification=True)
        except TelegramForbiddenError:
            logger.info("Bot bloklangan yoki chat ochilmagan")
            return
        anchor = marker.message_id
        try:
            await bot.delete_message(args.chat, anchor)
        except Exception:
            pass
        logger.info(f"chat={args.chat}, anchor={anchor}, {args.window} ta ID tekshiriladi\n")

        for step in range(1, args.window + 1):
            message_id = anchor - step
            if message_id <= 0:
                break
            try:
                message = await bot.forward_message(
                    chat_id=args.target,
                    from_chat_id=args.chat,
                    message_id=message_id,
                    disable_notification=True,
                )
            except TelegramRetryAfter as error:
                await asyncio.sleep(error.retry_after + 1)
                continue
            except Exception:
                await asyncio.sleep(args.delay)
                continue

            found.append((message_id,) + describe(message))
            try:
                await bot.delete_message(args.target, message.message_id)
            except Exception:
                pass
            await asyncio.sleep(args.delay)
    finally:
        await bot.session.close()

    logger.info(f"Topildi: {len(found)} ta xabar\n")
    logger.info(f"{'sana':<17} {'kim':<14} {'tur':<12} matn")
    logger.info("-" * 90)
    for message_id, date, author, content_type, text in sorted(found):
        if args.only_user and author == "bot":
            continue
        when = date.strftime("%Y-%m-%d %H:%M") if date else "?"
        logger.info(f"{when:<17} {author:<14} {content_type:<12} {text[:60]}")


if __name__ == "__main__":
    asyncio.run(main())
