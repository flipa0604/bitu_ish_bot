import gspread
import logging
import datetime
from data.config import SERVICE_ACCOUNT
from gspread import service_account
from gspread.exceptions import APIError, SpreadsheetNotFound
from google.oauth2.service_account import Credentials
from typing import Optional, Union



logger = logging.getLogger(__name__)
def get_worksheet(sheet_name: str):
    """
    Get a worksheet by its name from the Google Sheets document.
    
    :param sheet_name: The name of the worksheet to retrieve.
    :return: The Worksheet object if found, otherwise None.
    """
    try:
        gc = service_account(filename="service_account.json", scopes=["https://www.googleapis.com/auth/spreadsheets"])
        spreadsheet = gc.open_by_key("1d0uXjXTIHKyUaIIPm_fUomzUS3elK4TfTvcLpWIBzh8")
        return spreadsheet.worksheet(sheet_name)
    except (APIError, SpreadsheetNotFound):
        return None

def get_user_found_by_telegram_id(telegram_id: int) -> bool:
    """
    Check if user exists by their Telegram ID.
    
    :param telegram_id: The Telegram ID of the user.
    :return: True if user found, False otherwise.
    """
    worksheet = get_worksheet('Topshirganlar')
    if not worksheet:
        return False
    
    try:
        cell = worksheet.find(str(telegram_id))
        return bool(cell)
    except APIError:
        return False

SCOPE = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = 'service_account.json'  # O'z fayl yo'lingizni qo'ying
SPREADSHEET_ID = '1d0uXjXTIHKyUaIIPm_fUomzUS3elK4TfTvcLpWIBzh8'  # Google Sheets ID sini qo'ying


def get_google_sheets_client():
    """Google Sheets clientini olish"""
    try:
        creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPE)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        print(f"Google Sheets clientini olishda xatolik: {e}")
        return None

def save_to_google_sheets(user_data):
    """gspread kutubxonasi yordamida saqlash"""
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
        SHEET_ID = '1d0uXjXTIHKyUaIIPm_fUomzUS3elK4TfTvcLpWIBzh8'
        
        credentials = Credentials.from_service_account_file(
            'service_account.json',
            scopes=SCOPES
        )
        
        client = gspread.authorize(credentials)
        sheet = client.open_by_key(SHEET_ID).worksheet('Topshirganlar')
        
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
    worksheet = get_worksheet('Topshirganlar')
    if not worksheet:
        return None
    
    try:
        cell = worksheet.find(str(telegram_id))
        row = worksheet.row_values(cell.row)
        headers = worksheet.row_values(1)
        user_data = dict(zip(headers, row))
        return user_data
    except APIError:
        return None