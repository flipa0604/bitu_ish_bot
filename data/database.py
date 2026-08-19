import gspread
import logging
from data.config import SHEET_ID, SHEET_TAB_NAME, SERVICE_ACCOUNT_FILE
from gspread import service_account
from gspread.exceptions import APIError, SpreadsheetNotFound
from google.oauth2.service_account import Credentials
from typing import Optional


logger = logging.getLogger(__name__)

SCOPE = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

# Ovozli xabar va video xabar Telegram file_id ustunlari.
# file_id — bu Telegram fayl identifikatori, u orqali bot faylni istalgan vaqtda
# qayta yubora oladi (URL kabi 1 soatdan keyin eskirmaydi).
VOICE_HEADER = "Ovozli xabar"
VIDEO_HEADER = "Video xabar"

# Sheet ustunlari (tartibi bilan) va ularga mos user_data kalitlari
FIELD_MAP = [
    ("Ism Familya", "full_name"),
    ("Telefon", "phone_number"),
    ("Manzil", "address"),
    ("Tug'ilgan sana", "birth_date"),
    ("Ma'lumoti", "education"),
    ("Ish tajriba", "work_experience"),
    ("Oilaviy Holat", "marital_status"),
    ("Lavozimi", "position"),
    ("Rus tilini bilishi", "russian_level"),
    ("Ingliz tilini bilishi", "english_level"),
    ("Kutayotgan maosh", "salary_expectation"),
    ("Aloqa ma'lumoti", "reference_check"),
    ("Ish muddati", "work_duration"),
    ("Qo'shimcha ish", "overtime_work"),
    ("Ish sabablari", "work_reasons"),
    ("Sog'liq holati", "health_status"),
    ("Kechikish sababi", "question_some_workers_late_to_work"),
    ("O'g'irlik sababi", "question_what_workers_can_thief_answer"),
    ("Ish sifati sababi", "question_what_workers_good_works_some_bad"),
    ("Oldingi maosh", "question_previous_salary"),
    ("O'qigan kurslari", "courses_completed"),
    ("Qabul qilindi", None),
    ("TelegramID", "telegram_id"),
    (VOICE_HEADER, "voice_file_id"),
    (VIDEO_HEADER, "video_note_file_id"),
]

HEADERS = [header for header, _ in FIELD_MAP]


def get_worksheet(sheet_name: str):
    try:
        gc = service_account(filename=SERVICE_ACCOUNT_FILE, scopes=["https://www.googleapis.com/auth/spreadsheets"])
        spreadsheet = gc.open_by_key(SHEET_ID)
        return spreadsheet.worksheet(sheet_name)
    except (APIError, SpreadsheetNotFound):
        return None


def get_user_found_by_telegram_id(telegram_id: int) -> bool:
    worksheet = get_worksheet(SHEET_TAB_NAME)
    if not worksheet:
        return False
    try:
        cell = worksheet.find(str(telegram_id))
        return bool(cell)
    except APIError:
        return False


def get_google_sheets_client():
    try:
        creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPE)
        return gspread.authorize(creds)
    except Exception as e:
        logger.error(f"Google Sheets clientini olishda xatolik: {e}")
        return None


def ensure_headers(worksheet=None) -> list:
    """Sheet sarlavhalarini tekshiradi, yetishmayotganlarini oxiriga qo'shadi.

    Mavjud ustunlar va ma'lumotlar tegilmaydi — faqat yangi ustunlar qo'shiladi.
    Sheet sarlavhalari ro'yxatini qaytaradi.
    """
    worksheet = worksheet or get_worksheet(SHEET_TAB_NAME)
    if not worksheet:
        return []

    try:
        headers = [h for h in worksheet.row_values(1)]
    except APIError as e:
        logger.error(f"Sarlavhalarni o'qishda xatolik: {e}")
        return []

    if not headers:
        # Sheet butunlay bo'sh — barcha sarlavhalarni yozamiz
        if worksheet.col_count < len(HEADERS):
            worksheet.add_cols(len(HEADERS) - worksheet.col_count)
        worksheet.insert_row(HEADERS, index=1)
        logger.info("Sheet sarlavhalari yaratildi")
        return list(HEADERS)

    missing = [h for h in HEADERS if h not in headers]
    if not missing:
        return headers

    try:
        need = len(headers) + len(missing)
        if worksheet.col_count < need:
            worksheet.add_cols(need - worksheet.col_count)
        for offset, header in enumerate(missing, start=1):
            worksheet.update_cell(1, len(headers) + offset, header)
        logger.info(f"Sheetga yangi ustunlar qo'shildi: {missing}")
        return headers + missing
    except APIError as e:
        logger.error(f"Yangi ustunlarni qo'shishda xatolik: {e}")
        return headers


def save_to_google_sheets(user_data):
    try:
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
        credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        client = gspread.authorize(credentials)
        sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_TAB_NAME)

        # Ovozli/video ustunlari yo'q bo'lsa — qo'shib qo'yamiz
        headers = ensure_headers(sheet)
        if not headers:
            headers = list(HEADERS)

        # Ma'lumotlarni sarlavhalarga qarab tayyorlash (ustunlar tartibi o'zgarsa ham to'g'ri tushadi)
        values_by_header = {}
        for header, key in FIELD_MAP:
            if header == "Qabul qilindi":
                values_by_header[header] = False
            else:
                values_by_header[header] = user_data.get(key, '')

        row_data = [values_by_header.get(header, '') for header in headers]

        sheet.append_row(row_data)
        logger.info("Ma'lumotlar muvaffaqiyatli saqlandi (gspread)")
        return True

    except Exception as e:
        logger.error(f"gspread bilan saqlashda xatolik: {e}")
        return False


def get_user_data_by_telegram_id(telegram_id: int) -> Optional[dict]:
    """
    Get user data by their Telegram ID.

    :param telegram_id: The Telegram ID of the user.
    :return: A dictionary with user data if found, otherwise None.
    """
    worksheet = get_worksheet(SHEET_TAB_NAME)
    if not worksheet:
        return None

    try:
        cell = worksheet.find(str(telegram_id))
        row = worksheet.row_values(cell.row)
        headers = worksheet.row_values(1)
        return dict(zip(headers, row))
    except APIError:
        return None


def get_all_applications() -> list:
    """Sheetdagi barcha arizalarni ro'yxat (dict) ko'rinishida qaytaradi.

    Har bir dict qo'shimcha '_row' kaliti bilan keladi — bu sheetdagi qator raqami.
    """
    worksheet = get_worksheet(SHEET_TAB_NAME)
    if not worksheet:
        return []

    try:
        values = worksheet.get_all_values()
    except APIError as e:
        logger.error(f"Arizalarni o'qishda xatolik: {e}")
        return []

    if not values:
        return []

    headers = values[0]
    applications = []
    for row_number, row in enumerate(values[1:], start=2):
        if not any((cell or '').strip() for cell in row):
            continue
        item = {}
        for index, header in enumerate(headers):
            if not header:
                continue
            item[header] = row[index] if index < len(row) else ''
        item['_row'] = row_number
        applications.append(item)

    return applications
