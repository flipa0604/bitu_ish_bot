from aiogram import Router
from aiogram.enums import ChatType

from filters import ChatTypeFilter


def setup_routers() -> Router:
    from .users import admin, start, help, check_job, applications
    from .errors import error_handler

    router = Router()

    # Agar kerak bo'lsa, o'z filteringizni o'rnating
    start.router.message.filter(ChatTypeFilter(chat_types=[ChatType.PRIVATE]))

    router.include_routers(
        admin.router,
        applications.router,
        start.router,
        check_job.router,
        help.router,
        error_handler.router,
    )

    return router
