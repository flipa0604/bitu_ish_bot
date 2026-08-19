from aiogram import Router, types
from aiogram.filters.command import Command

from data.config import ADMINS

router = Router()


@router.message(Command('help'))
async def bot_help(message: types.Message):
    text = ["Buyruqlar: ",
            "/start - Botni ishga tushirish",
            "/help - Yordam"]

    if str(message.from_user.id) in [str(admin_id) for admin_id in ADMINS]:
        text += ["",
                 "Adminlar uchun:",
                 "/admin - Admin menyu",
                 "/arizalar - Arizalar ro'yxati"]

    await message.answer(text="\n".join(text))
