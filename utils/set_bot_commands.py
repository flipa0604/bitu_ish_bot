import logging

from aiogram import Bot
from aiogram.methods.set_my_commands import BotCommand
from aiogram.types import BotCommandScopeAllPrivateChats, BotCommandScopeChat

from data.config import ADMINS

logger = logging.getLogger(__name__)


async def set_default_commands(bot: Bot):
    commands = [
        BotCommand(command="/start", description="Botni ishga tushirish"),
        BotCommand(command="/help", description="Yordam"),
    ]
    await bot.set_my_commands(commands=commands, scope=BotCommandScopeAllPrivateChats())

    # Adminlar uchun qo'shimcha buyruqlar
    admin_commands = commands + [
        BotCommand(command="/admin", description="Admin menyu"),
        BotCommand(command="/arizalar", description="Arizalar ro'yxati"),
    ]
    for admin_id in ADMINS:
        try:
            await bot.set_my_commands(
                commands=admin_commands,
                scope=BotCommandScopeChat(chat_id=int(admin_id)),
            )
        except Exception as error:
            logger.warning(f"Admin {admin_id} uchun buyruqlar o'rnatilmadi: {error}")
