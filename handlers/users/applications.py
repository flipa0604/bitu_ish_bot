"""Admin menyusi: topshirilgan arizalarni ko'rish va yuborish."""

import asyncio
import logging
import time

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from data.config import ADMINS
from data.database import get_all_applications
from filters.admin import IsBotAdminFilter
from utils.applications import application_title, send_full_application

router = Router()
logger = logging.getLogger(__name__)

PAGE_SIZE = 8
CACHE_TTL = 60  # soniya
DELAY_BETWEEN_APPLICATIONS = 0.7

_cache = {"ts": 0.0, "items": []}
_bulk_sending = set()


async def load_applications(force: bool = False) -> list:
    """Arizalarni Google Sheetsdan oladi (60 soniyalik keshlash bilan)."""
    now = time.monotonic()
    if force or not _cache["items"] or (now - _cache["ts"]) > CACHE_TTL:
        items = await asyncio.to_thread(get_all_applications)
        if items or force:
            _cache["items"] = items
            _cache["ts"] = now
    return _cache["items"]


def menu_keyboard(count: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"📋 Arizalar ro'yxati ({count} ta)", callback_data="apps:list:0")],
        [InlineKeyboardButton(text="📤 Hammasini yuborish", callback_data="apps:all")],
        [InlineKeyboardButton(text="🔄 Yangilash", callback_data="apps:refresh")],
    ])


def list_keyboard(items: list, page: int) -> InlineKeyboardMarkup:
    total_pages = max(1, (len(items) + PAGE_SIZE - 1) // PAGE_SIZE)
    page = max(0, min(page, total_pages - 1))
    chunk = items[page * PAGE_SIZE:(page + 1) * PAGE_SIZE]

    rows = [
        [InlineKeyboardButton(
            text=f"{number}. {application_title(app)}",
            callback_data=f"apps:one:{app['_row']}",
        )]
        for number, app in enumerate(chunk, start=page * PAGE_SIZE + 1)
    ]

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"apps:list:{page - 1}"))
    nav.append(InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="apps:noop"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton(text="➡️", callback_data=f"apps:list:{page + 1}"))
    rows.append(nav)
    rows.append([InlineKeyboardButton(text="🏠 Admin menyu", callback_data="apps:menu")])

    return InlineKeyboardMarkup(inline_keyboard=rows)


def back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🔙 Ro'yxatga qaytish", callback_data="apps:list:0"),
        InlineKeyboardButton(text="🏠 Admin menyu", callback_data="apps:menu"),
    ]])


def menu_text(count: int) -> str:
    return (
        "👨‍💼 <b>Admin menyu</b>\n\n"
        f"Jami topshirilgan arizalar: <b>{count} ta</b>\n\n"
        "• <b>Arizalar ro'yxati</b> — kerakli arizani tanlab, to'liq ma'lumotini "
        "(ovozli xabari va videosi bilan) olasiz\n"
        "• <b>Hammasini yuborish</b> — barcha arizalar ketma-ket yuboriladi"
    )


@router.message(Command('admin'), IsBotAdminFilter(ADMINS))
async def admin_menu(message: types.Message):
    await message.bot.send_chat_action(message.chat.id, "typing")
    items = await load_applications()
    await message.answer(menu_text(len(items)), reply_markup=menu_keyboard(len(items)))


@router.message(Command('arizalar'), IsBotAdminFilter(ADMINS))
async def applications_command(message: types.Message):
    await message.bot.send_chat_action(message.chat.id, "typing")
    items = await load_applications()
    if not items:
        await message.answer("📭 Hozircha birorta ariza topilmadi.")
        return
    await message.answer(
        f"📋 <b>Arizalar ro'yxati</b> ({len(items)} ta)\n\nKerakli arizani tanlang:",
        reply_markup=list_keyboard(items, 0),
    )


@router.callback_query(F.data == "apps:noop", IsBotAdminFilter(ADMINS))
async def noop(call: types.CallbackQuery):
    await call.answer()


@router.callback_query(F.data.in_({"apps:menu", "apps:refresh"}), IsBotAdminFilter(ADMINS))
async def back_to_menu(call: types.CallbackQuery):
    force = call.data == "apps:refresh"
    await call.answer("Yangilanmoqda..." if force else None)
    items = await load_applications(force=force)
    text = menu_text(len(items))
    try:
        await call.message.edit_text(text, reply_markup=menu_keyboard(len(items)))
    except Exception:
        await call.message.answer(text, reply_markup=menu_keyboard(len(items)))


@router.callback_query(F.data.startswith("apps:list:"), IsBotAdminFilter(ADMINS))
async def show_list(call: types.CallbackQuery):
    await call.answer()
    page = int(call.data.rsplit(":", 1)[1])
    items = await load_applications()
    if not items:
        await call.message.answer("📭 Hozircha birorta ariza topilmadi.")
        return

    text = f"📋 <b>Arizalar ro'yxati</b> ({len(items)} ta)\n\nKerakli arizani tanlang:"
    try:
        await call.message.edit_text(text, reply_markup=list_keyboard(items, page))
    except Exception:
        await call.message.answer(text, reply_markup=list_keyboard(items, page))


@router.callback_query(F.data.startswith("apps:one:"), IsBotAdminFilter(ADMINS))
async def show_one(call: types.CallbackQuery):
    await call.answer("Yuborilmoqda...")
    row = int(call.data.rsplit(":", 1)[1])
    items = await load_applications()
    app, number = None, 0
    for index, item in enumerate(items, start=1):
        if item.get('_row') == row:
            app, number = item, index
            break
    if not app:
        await call.message.answer("❌ Ariza topilmadi. '🔄 Yangilash' tugmasini bosib ko'ring.")
        return

    await send_full_application(
        call.bot,
        call.message.chat.id,
        app,
        title=f"📄 <b>Ariza #{number}</b>",
    )
    await call.message.answer("Yana ariza tanlashingiz mumkin 👇", reply_markup=back_keyboard())


@router.callback_query(F.data == "apps:all", IsBotAdminFilter(ADMINS))
async def confirm_send_all(call: types.CallbackQuery):
    await call.answer()
    items = await load_applications()
    if not items:
        await call.message.answer("📭 Hozircha birorta ariza topilmadi.")
        return

    # har bir ariza: matn + ovoz + video (~2 soniya)
    minutes = max(1, round(len(items) * 2 / 60))
    text = (
        f"📤 <b>{len(items)} ta ariza</b> to'liq ma'lumoti, ovozli xabari va videosi bilan yuboriladi.\n\n"
        f"⏳ Taxminan {minutes} daqiqa vaqt oladi. Davom etamizmi?"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Ha, yubor", callback_data="apps:all_yes"),
        InlineKeyboardButton(text="❌ Bekor qilish", callback_data="apps:menu"),
    ]])
    try:
        await call.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        await call.message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "apps:all_yes", IsBotAdminFilter(ADMINS))
async def send_all(call: types.CallbackQuery):
    chat_id = call.message.chat.id
    if chat_id in _bulk_sending:
        await call.answer("Avvalgi yuborish hali tugamadi.", show_alert=True)
        return

    await call.answer()
    items = await load_applications()
    if not items:
        await call.message.answer("📭 Hozircha birorta ariza topilmadi.")
        return

    _bulk_sending.add(chat_id)
    status = await call.message.answer(f"📤 Yuborilmoqda... 0/{len(items)}")
    sent = 0
    failed = 0
    try:
        for number, app in enumerate(items, start=1):
            try:
                await send_full_application(
                    call.bot,
                    chat_id,
                    app,
                    title=f"📄 <b>Ariza #{number}/{len(items)}</b>",
                )
                sent += 1
            except Exception as error:
                failed += 1
                logger.error(f"Ariza #{number} yuborilmadi: {error}")

            if number % 5 == 0 or number == len(items):
                try:
                    await status.edit_text(f"📤 Yuborilmoqda... {number}/{len(items)}")
                except Exception:
                    pass
            await asyncio.sleep(DELAY_BETWEEN_APPLICATIONS)
    finally:
        _bulk_sending.discard(chat_id)

    summary = f"✅ Yuborildi: <b>{sent} ta</b>"
    if failed:
        summary += f"\n⚠️ Yuborilmadi: <b>{failed} ta</b>"
    await call.message.answer(summary, reply_markup=back_keyboard())
