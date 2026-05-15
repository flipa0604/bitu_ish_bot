import gspread
import logging
from data.config import SHEET_ID, SHEET_TAB_NAME, SERVICE_ACCOUNT_FILE
from gspread import service_account
from gspread.exceptions import APIError, SpreadsheetNotFound
from google.oauth2.service_account import Credentials
from typing import Optional


logger = logging.getLogger(__name__)

SCOPE = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']


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


def save_to_google_sheets(user_data):
    try:
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
        credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        client = gspread.authorize(credentials)
        sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_TAB_NAME)
        
        # Ma'lumotlarni tayyorlash
        row_data = [
            user_data.get('full_name', ''),
            user_data.get('phone_number', ''),
            user_data.get('address', ''),
            user_data.get('birth_date', ''),
            user_data.get('education', ''),
            user_data.get('work_experience', ''),
            user_data.get('marital_status', ''),
            user_data.get('position', ''),
            user_data.get('russian_level', ''),
            user_data.get('english_level', ''),
            user_data.get('salary_expectation', ''),
            user_data.get('reference_check', ''),
            user_data.get('work_duration', ''),
            user_data.get('overtime_work', ''),
            user_data.get('work_reasons', ''),
            user_data.get('health_status', ''),
            user_data.get('question_some_workers_late_to_work', ''),
            user_data.get('question_what_workers_can_thief_answer', ''),
            user_data.get('question_what_workers_good_works_some_bad', ''),
            user_data.get('question_previous_salary', ''),
            user_data.get('courses_completed', ''),
            user_data.get('about_yourself', ''),
            user_data.get('personal_qualities', ''),
            False,  # Qabul qilindi
            user_data.get('telegram_id', '')
        ]
        
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