from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def _normalize(text: str) -> str:
    result = text.lower()
    for ch in [" ", "-"]:
        result = result.replace(ch, "_")
    for ch in ["'", "`", "(", ")", ".", ":"]:
        result = result.replace(ch, "")
    return result


def _build_keyboard(positions, back_callback="back_to_departments"):
    buttons = [
        [InlineKeyboardButton(text=p, callback_data=f"position_{_normalize(p)}")]
        for p in positions
    ]
    buttons.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data=back_callback)])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def department_selection_keyboard():
    buttons = []
    departments = [
        "Ma'muriyat", "O'qituvchi", "Texnik xodim",
    ]
    
    for department in departments:
        department_call = department
        department_call = department_call.replace("'", "")
        department_call = department_call.replace(" ", "_")
        department_call = department_call.replace("-", "_")
        department_call = department_call.replace("(", "")
        department_call = department_call.replace(")", "")
        department_call = department_call.replace(".", "")
        department_call = department_call.replace("`", "")
        department_call = department_call.replace(":", "")
        department_call = department_call.lower()

        buttons.append([InlineKeyboardButton(text=department, callback_data=f"department_{department_call}")])
    
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def mamuriyat_position_keyboard():
    buttons = []
    positions = [
        "Direktor", "Boshqaruvchi", "Moliyachi", "Hisobchi",
        "Kadrlar bo'limi", "Marketing bo'limi", "IT bo'limi", "HR", "Tyutor", "Kotiba", "Yurist", "Prorektor"
    ]
    
    for position in positions:
        call_position = position.replace(" ", "_").lower()
        call_position = call_position.replace("'", "").lower()
        call_position = call_position.replace("-", "_").lower()
        call_position = call_position.replace("(", "").lower()
        call_position = call_position.replace(")", "").lower()
        call_position = call_position.replace(".", "").lower()

        buttons.append([InlineKeyboardButton(text=position, callback_data=f"position_{call_position}")])
    
    buttons.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_departments")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def texnik_xodim_position_keyboard():
    buttons = []
    positions = [
        "Elektrik", "Santexnik", "Usta", "Kompyuter mutaxassisi",
        "Qorovul", "Tozalovchi", "Bog'bon", "EHM operatori", "Kutubxonachi", "Komendant"
    ]
    
    for position in positions:
        buttons.append([InlineKeyboardButton(text=position, callback_data=f"position_{position}")])
    
    buttons.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_departments")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def talim_darajasi_keyboard():
    buttons = [
        [InlineKeyboardButton(text="Oliy ma'lumot", callback_data="education_higher")],
        [InlineKeyboardButton(text="O'rta maxsus ma'lumot", callback_data="education_specialized")],
        [InlineKeyboardButton(text="O'rta ma'lumot", callback_data="education_secondary")],
        [InlineKeyboardButton(text="Bakalavr", callback_data="education_bachelor")],
        [InlineKeyboardButton(text="Magistr", callback_data="education_master")],
        [InlineKeyboardButton(text="PhD", callback_data="education_phd")],
        [InlineKeyboardButton(text="Doktorantura", callback_data="education_doctorate")],
        [InlineKeyboardButton(text="Hozir o'qiyotgan", callback_data="education_currently_studying")],

        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_departments")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def oilaviy_holati():
    buttons = [
        [InlineKeyboardButton(text="Turmush qurgan", callback_data="marital_married")],
        [InlineKeyboardButton(text="Turmush qurmagan", callback_data="marital_single")],
        [InlineKeyboardButton(text="Ajrashgan", callback_data="marital_divorced")],
        [InlineKeyboardButton(text="Vafot etgan", callback_data="marital_widowed")],
        [InlineKeyboardButton(text="Bo'sh", callback_data="marital_empty")],
        
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_departments")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def ingliz_tili_bilish():
    buttons = [
        [InlineKeyboardButton(text="Yuqori daraja", callback_data="english_level_high")],
        [InlineKeyboardButton(text="O'rta daraja", callback_data="english_level_medium")],
        [InlineKeyboardButton(text="Past daraja", callback_data="english_level_low")],
        [InlineKeyboardButton(text="Bilmayman", callback_data="english_level_unknown")],
        
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_departments")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def rus_tili_bilish():
    buttons = [
        [InlineKeyboardButton(text="Yuqori daraja", callback_data="russian_level_high")],
        [InlineKeyboardButton(text="O'rta daraja", callback_data="russian_level_medium")],
        [InlineKeyboardButton(text="Past daraja", callback_data="russian_level_low")],
        [InlineKeyboardButton(text="Bilmayman", callback_data="russian_level_unknown")],
        
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_departments")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def ish_duration_keyboard():
    buttons = [
        [InlineKeyboardButton(text="1 yildan kam", callback_data="work_duration_less_than_1_year")],
        [InlineKeyboardButton(text="1-3 yil", callback_data="work_duration_1_to_3_years")],
        [InlineKeyboardButton(text="3-5 yil", callback_data="work_duration_3_to_5_years")],
        [InlineKeyboardButton(text="5 yildan ko'p", callback_data="work_duration_more_than_5_years")],
        
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_departments")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def oquvtchi_position_keyboard():
    positions = [
        "Klinik fanlar",
        "Ijtimoiy-gumanitar fanlar",
        "Tabiiy fanlar",
        "Aniq fanlar",
        "Texnik fanlar",
    ]
    return _build_keyboard(positions)


def klinik_fanlar_position_keyboard():
    positions = [
        "Terapiya", "Pediatriya", "Stomatologiya", "Ginekologiya",
        "Urologiya", "Oftalmologiya", "Psixiatriya", "Narkologiya",
    ]
    return _build_keyboard(positions)


def ijtimoiy_gumanitar_fanlar_position_keyboard():
    positions = [
        "Tarix", "Falsafa", "Sotsiologiya", "Psixologiya",
        "Pedagogika", "Iqtisodiyot", "Huquqshunoslik",
    ]
    return _build_keyboard(positions)


def tabiiy_fanlar_position_keyboard():
    positions = [
        "Biologiya", "Kimyo", "Fizika", "Geografiya",
        "Ekologiya", "Astronomiya",
    ]
    return _build_keyboard(positions)


def aniq_fanlar_position_keyboard():
    positions = [
        "Matematika", "Informatika", "Statistika", "Kibernetika",
        "Molekulyar biologiya", "Genetika",
    ]
    return _build_keyboard(positions)


def texnik_fanlar_position_keyboard():
    positions = [
        "Mexanika", "Elektronika", "Avtomatika", "Robototexnika",
        "Materialshunoslik", "Energetika",
    ]
    return _build_keyboard(positions)