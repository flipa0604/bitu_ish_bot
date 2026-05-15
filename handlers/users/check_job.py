from aiogram import types, Router
from data.database import get_user_data_by_telegram_id
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

router = Router()

@router.message(Command('check_job'))
async def check_job(message: types.Message):
    telegram_id = message.from_user.id
    user_data = get_user_data_by_telegram_id(telegram_id)
    if user_data:
        full_name = user_data.get('Ism Familya', 'Noma\'lum')
        position = user_data.get('Lavozimi', 'Noma\'lum')
        status = "✅ Qabul qilindi" if user_data.get('Qabul qilindi', False) else "⏳ Qabul qilinmadi yoki tekshirilmoqda "
        
        response_text = (
            f"Ismingiz: {full_name}\n"
            f"Lavozimingiz: {position}\n"
            f"Status: {status}"
        )
    else:
        response_text = "✍️ Sizning ish arizangiz topilmadi."
    await message.answer(response_text)

