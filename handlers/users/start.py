import logging
from aiogram import Router, types, F
from aiogram.filters import CommandStart
from data.config import ADMINS
from data.database import get_user_found_by_telegram_id, save_to_google_sheets
from keyboards.inline.start import (
    department_selection_keyboard,
    mamuriyat_position_keyboard,
    oquvtchi_position_keyboard,
    texnik_xodim_position_keyboard,
    klinik_fanlar_position_keyboard,
    ijtimoiy_gumanitar_fanlar_position_keyboard,
    tabiiy_fanlar_position_keyboard,
    aniq_fanlar_position_keyboard,
    texnik_fanlar_position_keyboard,
    talim_darajasi_keyboard,
    oilaviy_holati,
    ingliz_tili_bilish,
    rus_tili_bilish,
    ish_duration_keyboard,
    ) 

from states.start import UserRegistration
from aiogram.fsm.context import FSMContext
from utils.applications import escape_html, send_application_media, send_long_message


router = Router()
logger = logging.getLogger(__name__)


async def notify_admins(bot, user_data: dict, from_user):
    """Yangi ariza haqida adminlarga to'liq ma'lumot + ovozli xabar va videoni yuborish."""
    username = f"@{from_user.username}" if from_user.username else "—"
    text = (
        f"🆕 <b>Yangi ariza topshirildi!</b>\n\n"
        f"👤 <b>Ism:</b> {escape_html(user_data.get('full_name'))}\n"
        f"📞 <b>Telefon:</b> {escape_html(user_data.get('phone_number'))}\n"
        f"🏠 <b>Manzil:</b> {escape_html(user_data.get('address'))}\n"
        f"🎂 <b>Tug'ilgan sana:</b> {escape_html(user_data.get('birth_date'))}\n"
        f"🎓 <b>Ta'lim:</b> {escape_html(user_data.get('education'))}\n"
        f"💼 <b>Ish tajriba:</b> {escape_html(user_data.get('work_experience'))}\n"
        f"💍 <b>Oilaviy holat:</b> {escape_html(user_data.get('marital_status'))}\n"
        f"🎯 <b>Lavozim:</b> {escape_html(user_data.get('position'))}\n"
        f"🇬🇧 <b>Ingliz tili:</b> {escape_html(user_data.get('english_level'))}\n"
        f"🇷🇺 <b>Rus tili:</b> {escape_html(user_data.get('russian_level'))}\n"
        f"💰 <b>Kutilayotgan maosh:</b> {escape_html(user_data.get('salary_expectation'))}\n"
        f"📋 <b>Tavsiyachi:</b> {escape_html(user_data.get('reference_check'))}\n"
        f"⏰ <b>Ish muddati:</b> {escape_html(user_data.get('work_duration'))}\n"
        f"🕐 <b>Qo'shimcha ish:</b> {escape_html(user_data.get('overtime_work'))}\n"
        f"🎯 <b>Ish sababi:</b> {escape_html(user_data.get('work_reasons'))}\n"
        f"🏥 <b>Sog'liq:</b> {escape_html(user_data.get('health_status'))}\n"
        f"🐢 <b>Kechikish sababi:</b> {escape_html(user_data.get('question_some_workers_late_to_work'))}\n"
        f"🚨 <b>O'g'irlik sababi:</b> {escape_html(user_data.get('question_what_workers_can_thief_answer'))}\n"
        f"⚖️ <b>Ish sifati sababi:</b> {escape_html(user_data.get('question_what_workers_good_works_some_bad'))}\n"
        f"💸 <b>Oldingi maosh:</b> {escape_html(user_data.get('question_previous_salary'))}\n"
        f"📚 <b>Kurslar:</b> {escape_html(user_data.get('courses_completed'))}\n\n"
        f"👥 <b>Username:</b> {escape_html(username)}\n"
        f"🆔 <b>Telegram ID:</b> <code>{escape_html(user_data.get('telegram_id'))}</code>"
    )

    # Ovozli xabar va yumaloq video adminlarga havola emas, o'zi bo'lib boradi
    voice_file_id = user_data.get('voice_file_id')
    video_note_file_id = user_data.get('video_note_file_id')

    for admin_id in ADMINS:
        try:
            await send_long_message(bot, int(admin_id), text)
            await send_application_media(
                bot,
                int(admin_id),
                voice_file_id=voice_file_id,
                video_file_id=video_note_file_id,
                note_if_missing=False,
            )
        except Exception as e:
            logger.error(f"Admin {admin_id} ga xabar yuborilmadi: {e}")


@router.callback_query(F.data == "back_to_departments")
async def back_to_departments(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "Iltimos, quyidagi bo'limlardan birini tanlang:",
        reply_markup=department_selection_keyboard()
    )
    await callback.answer()


@router.message(CommandStart())
async def do_start(message: types.Message):
    """
            MARKDOWN V2                     |     HTML
    link:   [Google](https://google.com/)   |     <a href='https://google.com/'>Google</a>
    bold:   *Qalin text*                    |     <b>Qalin text</b>
    italic: _Yotiq shriftdagi text_         |     <i>Yotiq shriftdagi text</i>



                    **************     Note     **************
    Markdownda _ * [ ] ( ) ~ ` > # + - = | { } . ! belgilari to'g'ridan to'g'ri ishlatilmaydi!!!
    Bu belgilarni ishlatish uchun oldidan \ qo'yish esdan chiqmasin. Masalan  \.  ko'rinishi . belgisini ishlatish uchun yozilgan.
    """

    telegram_id = message.from_user.id
    video_url = "https://t.me/mycloud777/2"
    already_applied = get_user_found_by_telegram_id(telegram_id)

    # Ba'zi foydalanuvchilar maxfiylik sozlamasida ovozli/video xabarlarni yopib
    # qo'ygan (VOICE_MESSAGES_FORBIDDEN) — bunda tanishtiruv videosi yuborilmaydi,
    # lekin ariza jarayoni to'xtab qolmasligi kerak
    try:
        await message.bot.send_chat_action(message.chat.id, "upload_video")
        if already_applied:
            await message.answer_video_note(video_note=video_url)
        else:
            await message.answer_video(video=video_url)
    except Exception as error:
        logger.warning(f"Tanishtiruv videosi yuborilmadi ({telegram_id}): {error}")

    await message.bot.send_chat_action(message.chat.id, "typing")
    if already_applied:
        await message.answer(
            text="Assalomu alaykum, siz allaqachon botimizga hujjat topshirgan ekansiz! \n\n Albatta siz bilan bog'lanamiz😊",
        )
    else:
        await message.answer(
            text="Assalomu alaykum qaysi lavozimda ishlamoqchisiz?",
            reply_markup=department_selection_keyboard()
        )


@router.callback_query(F.data.startswith("department_"))
async def handle_department_selection(callback: types.CallbackQuery):
    department = callback.data.split("department_")[1]
    
    if department == "mamuriyat":
        await callback.message.edit_text(
            "Quyidagi lavozimlardan birini tanlang:",
            reply_markup=mamuriyat_position_keyboard()
        )
    elif department == "oqituvchi":
        await callback.message.edit_text(
            "Fan yo'nalishini tanlang:",
            reply_markup=oquvtchi_position_keyboard()
        )
    elif department == "texnik_xodim":
        await callback.message.edit_text(
            "Quyidagi lavozimlardan birini tanlang:",
            reply_markup=texnik_xodim_position_keyboard()
        )
    
    await callback.answer()




@router.callback_query(F.data.startswith("position_"))
async def handle_position_selection(callback: types.CallbackQuery, state: FSMContext):
    position = callback.data.split("position_")[1]
    
    # O'qituvchi yo'nalishlarining ichki fanlari
    if position == "klinik_fanlar":
        await callback.message.edit_text(
            "Fan yo'nalishini tanlang:",
            reply_markup=klinik_fanlar_position_keyboard()
        )
    elif position == "ijtimoiy_gumanitar_fanlar":
        await callback.message.edit_text(
            "Fan yo'nalishini tanlang:",
            reply_markup=ijtimoiy_gumanitar_fanlar_position_keyboard()
        )
    elif position == "tabiiy_fanlar":
        await callback.message.edit_text(
            "Fan yo'nalishini tanlang:",
            reply_markup=tabiiy_fanlar_position_keyboard()
        )
    elif position == "aniq_fanlar":
        await callback.message.edit_text(
            "Fan yo'nalishini tanlang:",
            reply_markup=aniq_fanlar_position_keyboard()
        )
    elif position == "texnik_fanlar":
        await callback.message.edit_text(
            "Fan yo'nalishini tanlang:",
            reply_markup=texnik_fanlar_position_keyboard()
        )
    else:
        # Boshqa lavozimlar uchun statega saqlash va savollarga o'tish
        await callback.message.bot.send_chat_action(callback.message.chat.id, "typing")
        await state.update_data(position=position)
        await state.set_state(UserRegistration.full_name)
        await callback.message.edit_text(
            f"Siz {position.replace('_', ' ').title()} lavozimini tanladingiz.\n"
            "01/23. Iltimos, to'liq ismingizni yuboring."
        )
    
    await callback.answer()

@router.message(UserRegistration.full_name)
async def handle_full_name(message: types.Message, state: FSMContext):
    full_name = (message.text or "").strip()
    await message.bot.send_chat_action(message.chat.id, "typing")
    if not full_name:
        await message.reply("Iltimos, to'liq ismingizni kiriting.")
        return
    
    # To'liq ismi saqlash
    await state.update_data(full_name=full_name)
    
    # Telefon raqamini so'rash
    await state.set_state(UserRegistration.phone_number)
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer(
        "02/23. Iltimos, telefon raqamingizni yuboring (masalan: +998901234567) yoki pastdagi tugmani bosing:",
        reply_markup=keyboard
    )

@router.message(UserRegistration.phone_number)
async def handle_phone_number(message: types.Message, state: FSMContext):
    await message.bot.send_chat_action(message.chat.id, "typing")
    if message.contact:
        phone_number = message.contact.phone_number
    else:
        phone_number = (message.text or "").strip()
    
    if not phone_number:
        await message.reply("Iltimos, telefon raqamingizni kiriting.")
        return
    
    # Telefon raqamini saqlash
    await state.update_data(phone_number=phone_number)
    
    # Manzilni so'rash
    await state.set_state(UserRegistration.address)
    await message.answer(
        "03/23. ✍️ Iltimos, manzilingizni kiriting (masalan: Farg'ona, Toshloq tumani, Ziyokor ko'chasi):"
    )

@router.message(UserRegistration.address)
async def handle_address(message: types.Message, state: FSMContext):
    address = (message.text or "").strip()
    await message.bot.send_chat_action(message.chat.id, "typing")
    
    if not address:
        await message.reply("Iltimos, manzilingizni kiriting.")
        return
    # Manzilni saqlash
    await state.update_data(address=address)
    # Tug'ilgan sanani so'rash
    await state.set_state(UserRegistration.birth_date)
    await message.answer(
        "04/23. Tug'ilgan sanangizni kiriting (masalan: 1990-01-01):"
    )

@router.message(UserRegistration.birth_date)
async def handle_birth_date(message: types.Message, state: FSMContext):
    birth_date = (message.text or "").strip()
    await message.bot.send_chat_action(message.chat.id, "typing")
    
    if not birth_date:
        await message.reply("Iltimos, tug'ilgan sanangizni kiriting.")
        return
    
    await state.update_data(birth_date=birth_date)
    await state.set_state(UserRegistration.education)
    await message.answer(
        "05/23. Ta'lim darajangizni tanlang (masalan: Oliy, O'rta maxsus):",
        reply_markup=talim_darajasi_keyboard()
    )

@router.callback_query(F.data.startswith("education_"))
async def handle_education_selection(callback: types.CallbackQuery, state: FSMContext):
    education = callback.data.split("education_")[1]
    await callback.message.bot.send_chat_action(callback.message.chat.id, "typing")
    # Education level translation
    education_translations = {
        "phd": "PhD",
        "masters": "Magistr", 
        "bachelors": "Bakalavr",
        "secondary": "O'rta maxsus",
        "high_school": "O'rta",
        "specialized": "O'rta maxsus",
        "currently_studying": "Hozir o'qiyotgan",
        "higher": "Oliy ma'lumot",
        "doctorate": "Doktorantura",
        "no_education": "Ta'lim yo'q"
        
    }
    
    translated_education = education_translations.get(education, education)
    await state.update_data(education=translated_education)
    
    await state.set_state(UserRegistration.work_experience)
    await callback.message.edit_text(
        "06/23. Ish tajribangizni kiriting (masalan: 5 yil):"
    )
    await callback.answer()

@router.message(UserRegistration.work_experience)
async def handle_work_experience(message: types.Message, state: FSMContext):
    work_experience = (message.text or "").strip()
    await message.bot.send_chat_action(message.chat.id, "typing")

    if not work_experience:
        await message.reply("Iltimos, ish tajribangizni kiriting.")
        return
    
    await state.update_data(work_experience=work_experience)
    await state.set_state(UserRegistration.marital_status)
    await message.answer(
        "07/23. Oila holatingizni tanlang (masalan: Uylangan, Bo'sh):",
        reply_markup=oilaviy_holati()
    )

@router.callback_query(F.data.startswith("marital_"))
async def handle_marital_status_selection(callback: types.CallbackQuery, state: FSMContext):
    marital_status = callback.data.split("marital_")[1]
    await callback.message.bot.send_chat_action(callback.message.chat.id, "typing")
    
    # Marital status translation
    status_translations = {
        "married": "Uylangan/Turmushga chiqqan",
        "single": "Bo'ydoq/Turmushga chiqmagan",
        "divorced": "Ajrashgan"
    }
    
    translated_status = status_translations.get(marital_status, marital_status)
    await state.update_data(marital_status=translated_status)
    
    await state.set_state(UserRegistration.english_level)
    await callback.message.edit_text(
        "08/23. Ingliz tilini qay darajada bilasiz?:",
        reply_markup=ingliz_tili_bilish()
    )
    await callback.answer()

@router.callback_query(F.data.startswith("english_level_"))
async def handle_english_level_selection(callback: types.CallbackQuery, state: FSMContext):
    english_level = callback.data.split("english_level_")[1]
    await callback.message.bot.send_chat_action(callback.message.chat.id, "typing")   
    # Language level translation
    level_translations = {
        "high": "Yuqori daraja",
        "medium": "O'rta daraja",
        "low": "Boshlang'ich daraja",
        "none": "Bilmayman"
    }
    
    translated_level = level_translations.get(english_level, english_level)
    await state.update_data(english_level=translated_level)
    
    await state.set_state(UserRegistration.russian_level)
    await callback.message.edit_text(
        "09/33. Rus tilini qay darajada bilasiz?:",
        reply_markup=rus_tili_bilish()
    )
    await callback.answer()

@router.callback_query(F.data.startswith("russian_level_"))
async def handle_russian_level_selection(callback: types.CallbackQuery, state: FSMContext):
    russian_level = callback.data.split("russian_level_")[1]
    await callback.message.bot.send_chat_action(callback.message.chat.id, "typing")
    # Language level translation
    level_translations = {
        "high": "Yuqori daraja",
        "medium": "O'rta daraja", 
        "low": "Boshlang'ich daraja",
        "none": "Bilmayman"
    }
    
    translated_level = level_translations.get(russian_level, russian_level)
    await state.update_data(russian_level=translated_level)
    
    await state.set_state(UserRegistration.salary_expectation)
    await callback.message.edit_text(
        "10/23. Ish haqidagi kutganingizni kiriting (masalan: 2000$):"
    )
    await callback.answer()


@router.message(UserRegistration.salary_expectation)
async def handle_salary_expectation(message: types.Message, state: FSMContext):
    salary_expectation = (message.text or "").strip()
    await message.bot.send_chat_action(message.chat.id, "typing")
    if not salary_expectation:
        await message.reply("Iltimos, ish haqidagi kutganingizni kiriting.")
        return
    
    # Ish haqidagi kutganingizni saqlash
    await state.update_data(salary_expectation=salary_expectation)
    
    # Tavsiyalarni tekshirish
    await state.set_state(UserRegistration.reference_check)
    await message.answer(
        "11/23. Oldin ishlagan joyingizdan tavsiyachini yozin yo'q bo'lsa (No) so'zini yozib ketin:\n\n" \
        "Misol: Direktor - Malika Akramovna - Nona collection - +998909998877",
        
    )

@router.message(UserRegistration.reference_check)
async def handle_reference_check(message: types.Message, state: FSMContext):
    reference_check = (message.text or "").strip()
    await message.bot.send_chat_action(message.chat.id, "typing")
    if not reference_check:
        await message.reply("Iltimos, tavsiyalarni kiriting.")
        return
    
    # Tavsiyalarni saqlash
    await state.update_data(reference_check=reference_check)
    
    # Ish joyi bilan bog'lanish uchun kontaktni so'rash
    await state.set_state(UserRegistration.work_duration)
    await message.answer(
        "12/23. Ish joyida qancha vaqt ishlashni rejalashtiryapsiz? (masalan: 6 oy, 1 yil):",
        reply_markup=ish_duration_keyboard()
    )

@router.callback_query(F.data.startswith("work_duration_"))
async def handle_work_duration_selection(callback: types.CallbackQuery, state: FSMContext):
    work_duration = callback.data.split("work_duration_")[1]
    await callback.message.bot.send_chat_action(callback.message.chat.id, "typing")
    # Duration translation
    duration_translations = {
        "less_than_1_year": "1 yildan kam",
        "1_to_3_years": "1-3 yil",
        "3_to_5_years": "3-5 yil", 
        "more_than_5_years": "5 yildan ko'p"
    }
    
    translated_duration = duration_translations.get(work_duration, work_duration)
    await state.update_data(work_duration=translated_duration)
    
    # Qo'shimcha ish soatlari haqida so'rash
    await state.set_state(UserRegistration.overtime_work)
    await callback.message.edit_text(
        "13/23. Qo'shimcha ish soatlarini bajarishga tayyormisiz? (Ha/Yo'q):"
    )
    
    await callback.answer()

@router.message(UserRegistration.overtime_work)
async def handle_overtime_work(message: types.Message, state: FSMContext):
    overtime_work = (message.text or "").strip().lower()
    await message.bot.send_chat_action(message.chat.id, "typing")
    if overtime_work not in ["ha", "yo'q"]:
        await message.reply("Iltimos, 'Ha' yoki 'Yo'q' deb javob bering.")
        return
    
    # Qo'shimcha ish soatlarini saqlash
    await state.update_data(overtime_work=overtime_work)
    
    # Ish joyini tanlash
    await state.set_state(UserRegistration.work_reasons)
    await message.answer(
        "14/23. Ish joyini tanlash sababi nima? (masalan: Yangi tajriba, Karyera o'sishi):"
    )

@router.message(UserRegistration.work_reasons)
async def handle_work_reasons(message: types.Message, state: FSMContext):
    work_reasons = (message.text or "").strip()
    await message.bot.send_chat_action(message.chat.id, "typing")
    if not work_reasons:
        await message.reply("Iltimos, ish joyini tanlash sababini kiriting.")
        return
    
    # Ish joyini tanlash sababini saqlash
    await state.update_data(work_reasons=work_reasons)
    
    # Shaxsiy sifatlarni so'rash
    video_url = "https://t.me/mycloud777/3"
    question = ("15/23. O'zingizni qanday shaxsiy sifatlaringiz bor deb o'ylaysiz? "
                "(masalan: Javobgarlik, Jamoada ishlash) \n\n⚠️ Video formatda!:")
    await state.set_state(UserRegistration.personal_qualities)
    try:
        await message.answer_video(video=video_url, caption=question)
    except Exception as error:
        # Video yuborilmasa ham savol nomzodga yetib borishi kerak
        logger.warning(f"Namuna video yuborilmadi: {error}")
        await message.answer(question)

@router.message(UserRegistration.personal_qualities)
async def handle_personal_qualities(message: types.Message, state: FSMContext):
    if not message.video_note:
        await message.answer("Iltimos, videoni yumaloq formatda yuboring.")
        return
    
    await message.bot.send_chat_action(message.chat.id, "typing")
    
    
    
    # Videoning file_id si saqlanadi — bot uni adminlarga istalgan vaqtda
    # qayta yubora oladi (havola 1 soatdan keyin eskirardi)
    await state.update_data(video_note_file_id=message.video_note.file_id)
    # Kurslar haqida so'rash
    await state.set_state(UserRegistration.courses_completed)
    await message.answer(
        "16/23. Qanday kurslarda o'qigansiz?:"
        )
@router.message(UserRegistration.courses_completed)
async def handle_courses_completed(message: types.Message, state: FSMContext):
    courses_completed = (message.text or "").strip()
    await message.bot.send_chat_action(message.chat.id, "typing")
    if not courses_completed:
        await message.reply("Iltimos, kurslar haqida ma'lumot kiriting.")
        return
    
    # Kurslar haqida ma'lumotni saqlash
    await state.update_data(courses_completed=courses_completed)
    
    # Sog'liq holatini so'rash
    await state.set_state(UserRegistration.health_status)
    await message.answer(
        "17/23. Sog'ligingizda muammo yo'qmi?:"
    )

@router.message(UserRegistration.health_status)
async def handle_health_status(message: types.Message, state: FSMContext):
    health_status = (message.text or "").strip().lower()
    await message.bot.send_chat_action(message.chat.id, "typing")
    if health_status not in ["ha", "yo'q"]:
        await message.reply("Iltimos, 'Ha' yoki 'Yo'q' deb javob bering.")
        return
    
    # Sog'liq holatini saqlash
    await state.update_data(health_status=health_status)
    
    # Savolga javob berish
    await state.set_state(UserRegistration.question_what_workers_can_thief_answer)
    await message.answer(
        "18/23. Nima uchun ayrim insonlar o'g'rilik qilishadi?"
    )

@router.message(UserRegistration.question_what_workers_can_thief_answer)
async def handle_thief_answer(message: types.Message, state: FSMContext):
    thief_answer = (message.text or "").strip()
    await message.bot.send_chat_action(message.chat.id, "typing")
    if not thief_answer:
        await message.reply("Iltimos, savolga javob bering.")
        return
    
    # Savolga javobni saqlash
    await state.update_data(question_what_workers_can_thief_answer=thief_answer)
    
    # Yana bir savol
    await state.set_state(UserRegistration.question_what_workers_good_works_some_bad)
    await message.answer(
        "19/23. Nima uchun ayrim ishchilar yaxshi ishlashadi, ayrimlari yomon? Bunga sabab nima?"
    )

@router.message(UserRegistration.question_what_workers_good_works_some_bad)
async def handle_good_bad_answer(message: types.Message, state: FSMContext):
    good_bad_answer = (message.text or "").strip()
    await message.bot.send_chat_action(message.chat.id, "typing")
    if not good_bad_answer:
        await message.reply("Iltimos, savolga javob bering.")
        return
    
    # Savolga javobni saqlash
    await state.update_data(question_what_workers_good_works_some_bad=good_bad_answer)
    
    # O'zingiz haqida ma'lumot berish

    await state.set_state(UserRegistration.about_yourself)
    try:
        await message.answer_audio(audio="https://t.me/mycloud777/4")
    except Exception as error:
        logger.warning(f"Namuna audio yuborilmadi: {error}")
    await message.answer(
        "20/23. Qarindoshlaringiz haqida qisqacha ma'lumot bering (🎤Ovoz ko'rinishida):"
    )

@router.message(UserRegistration.about_yourself)
async def handle_about_yourself(message: types.Message, state: FSMContext):
    if not message.voice:
        await message.answer("Iltimos, ovozli xabar yuboring.")
        return
    await message.bot.send_chat_action(message.chat.id, "typing")
    # Ovozli xabarning file_id si saqlanadi
    await state.update_data(voice_file_id=message.voice.file_id)

    # Shaxsiy sifatlar haqida ma'lumot berish
    
    await state.set_state(UserRegistration.question_some_workers_late_to_work)
    await message.answer(
        "21/23. Nima uchun ayrim ishchilar ishga kech kelishadi? Bunga sabab nima?"
        )    

@router.message(UserRegistration.question_some_workers_late_to_work)
async def handle_some_workers_late_to_work(message: types.Message, state: FSMContext):
    some_workers_late_to_work = (message.text or "").strip()
    await message.bot.send_chat_action(message.chat.id, "typing")
    if not some_workers_late_to_work:
        await message.reply("Iltimos, savolga javob bering.")
        return
    
    await state.update_data(question_some_workers_late_to_work=some_workers_late_to_work)

    await state.set_state(UserRegistration.question_previous_salary)
    await message.answer(
        "22/23. Oldingi ish joyingizdagi oylik maoshingiz qancha edi? (masalan: 1500$):"
    )

@router.message(UserRegistration.question_previous_salary)
async def handle_previous_salary(message: types.Message, state: FSMContext):
    previous_salary = (message.text or "").strip()
    await message.bot.send_chat_action(message.chat.id, "typing")
    if not previous_salary:
        await message.reply("Iltimos, oldingi ish joyingizdagi oylik maoshingizni kiriting.")
        return
    # Oldingi ish joyidagi maoshni saqlash
    await state.update_data(question_previous_salary=previous_salary)
    user_data = await state.get_data()
    
    # Telegram ID ni qo'shish
    user_data['telegram_id'] = message.from_user.id

    # Google Sheets ga saqlash
    saved = save_to_google_sheets(user_data)

    # Adminlarga to'liq ma'lumot yuborish (saqlash holatidan qat'iy nazar)
    try:
        await notify_admins(message.bot, user_data, message.from_user)
    except Exception as e:
        logger.error(f"Adminlarni xabardor qilishda xatolik: {e}")

    await state.clear()

    if saved:
        await message.answer("✅ Sizning ma'lumotlaringiz muvaffaqiyatli saqlandi!\n\nTez orada siz bilan bog'lanamiz.")
    else:
        await message.answer("⚠️ Ariza qabul qilindi, lekin saqlashda xatolik bo'ldi. Adminlar bilan bog'laning.")














    


# @router.callback_query(F.data.startswith("position_"))
# async def handle_position_selection(callback: types.CallbackQuery):
#     position = callback.data.split("position_")[1]

#     # O'qituvchi yo'nalishlarining ichki fanlari
#     if position == "klinik_fanlar":
#         await callback.message.edit_text(
#             "Fan yo'nalishini tanlang:",
#             reply_markup=klinik_fanlar_position_keyboard()
#         )
#     elif position == "ijtimoiy_gumanitar_fanlar":
#         await callback.message.edit_text(
#             "Fan yo'nalishini tanlang:",
#             reply_markup=ijtimoiy_gumanitar_fanlar_position_keyboard()
#         )
#     elif position == "tabiiy_fanlar":
#         await callback.message.edit_text(
#             "Fan yo'nalishini tanlang:",
#             reply_markup=tabiiy_fanlar_position_keyboard()
#         )
#     elif position == "aniq_fanlar":
#         await callback.message.edit_text(
#             "Fan yo'nalishini tanlang:",
#             reply_markup=aniq_fanlar_position_keyboard()
#         )
#     elif position == "texnik_fanlar":
#         await callback.message.edit_text(
#             "Fan yo'nalishini tanlang:",
#             reply_markup=texnik_fanlar_position_keyboard()
#         )
#     else:
#         # Boshqa lavozimlar
#         await callback.message.edit_text(
#             f"Siz {position.replace('_', ' ').title()} lavozimini tanladingiz.\n"
#             "Iltimos, rezyumeingizni yuboring."
#         )
    
#     await callback.answer()
