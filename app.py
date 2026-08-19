import asyncio
from google.oauth2 import service_account
from aiogram import Bot, Dispatcher
from googleapiclient.discovery import build
from aiogram.client.session.middlewares.request_logging import logger
from aiogram.enums import ChatType
from loader import db
from data.config import SHEET_ID, SHEET_TAB_NAME, SERVICE_ACCOUNT_FILE
from data.database import HEADERS, ensure_headers


def setup_handlers(dispatcher: Dispatcher) -> None:
    """HANDLERS"""
    from handlers import setup_routers

    dispatcher.include_router(setup_routers())


def setup_middlewares(dispatcher: Dispatcher, bot: Bot) -> None:
    """MIDDLEWARE"""
    from middlewares.throttling import ThrottlingMiddleware

    # Spamdan himoya qilish uchun klassik ichki o'rta dastur. So'rovlar orasidagi asosiy vaqtlar 0,5 soniya
    dispatcher.message.middleware(ThrottlingMiddleware(slow_mode_delay=0.5))


def setup_filters(dispatcher: Dispatcher) -> None:
    """FILTERS"""
    from filters import ChatTypeFilter

    # Chat turini aniqlash uchun klassik umumiy filtr
    # Filtrni handlers/users/__init__ -dagi har bir routerga alohida o'rnatish mumkin
    dispatcher.message.filter(ChatTypeFilter(chat_types=[ChatType.PRIVATE]))


async def setup_aiogram(dispatcher: Dispatcher, bot: Bot) -> None:
    logger.info("Configuring aiogram")
    setup_handlers(dispatcher=dispatcher)
    setup_middlewares(dispatcher=dispatcher, bot=bot)
    setup_filters(dispatcher=dispatcher)
    logger.info("Configured aiogram")


async def database_connected():
    """Google Sheets bilan ulanish va sheet yaratish"""
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

    try:
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE,
            scopes=SCOPES
        )
        
        service = build('sheets', 'v4', credentials=credentials)
        sheets = service.spreadsheets()

        # Spreadsheet mavjudligini tekshirish
        try:
            sheets.get(spreadsheetId=SHEET_ID).execute()
        except Exception:
            logger.error("Sheet ID not found")
            return

        # Headers - data/database.py dagi markaziy ro'yxatdan olinadi
        headers = list(HEADERS)

        try:
            # Avval sheet mavjudligini tekshirish
            spreadsheet = sheets.get(spreadsheetId=SHEET_ID).execute()
            sheet_exists = False
            
            for sheet in spreadsheet.get('sheets', []):
                if sheet['properties']['title'] == SHEET_TAB_NAME:
                    sheet_exists = True
                    logger.info(f"Sheet '{SHEET_TAB_NAME}' already exists")
                    break

            if sheet_exists:
                # Eski sheetda yangi ustunlar (Ovozli xabar / Video xabar) bo'lmasa qo'shiladi
                ensure_headers()
            
            if not sheet_exists:
                # Yangi sheet yaratish
                request = {
                    'requests': [{
                        'addSheet': {
                            'properties': {
                                'title': SHEET_TAB_NAME,
                                'gridProperties': {
                                    'rowCount': 1000,
                                    'columnCount': len(headers),
                                    'frozenRowCount': 1
                                }
                            }
                        }
                    }]
                }
                response = sheets.batchUpdate(spreadsheetId=SHEET_ID, body=request).execute()
                sheet_id = response['replies'][0]['addSheet']['properties']['sheetId']
                
                # Headers qo'shish - to'g'ri format
                sheets.values().update(
                    spreadsheetId=SHEET_ID,
                    range=f'{SHEET_TAB_NAME}!A1',
                    valueInputOption='RAW',
                    body={'values': [headers]}  # Bu yerda [headers] bo'lishi kerak
                ).execute()
                
                # Formatlash
                requests = [
                    # Header formatlash
                    {
                        'repeatCell': {
                            'range': {
                                'sheetId': sheet_id,
                                'startRowIndex': 0,
                                'endRowIndex': 1
                            },
                            'cell': {
                                'userEnteredFormat': {
                                    'backgroundColor': {'red': 0.2, 'green': 0.5, 'blue': 0.7},
                                    'textFormat': {
                                        'bold': True,
                                        'fontSize': 11,
                                        'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}
                                    },
                                    'horizontalAlignment': 'CENTER',
                                    'verticalAlignment': 'MIDDLE',
                                    'wrapStrategy': 'WRAP'
                                }
                            },
                            'fields': 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,wrapStrategy)'
                        }
                    },
                    # Chegaralar qo'shish
                    {
                        'updateBorders': {
                            'range': {
                                'sheetId': sheet_id,
                                'startRowIndex': 0,
                                'endRowIndex': 1000,
                                'startColumnIndex': 0,
                                'endColumnIndex': len(headers)
                            },
                            'top': {'style': 'SOLID', 'width': 1},
                            'bottom': {'style': 'SOLID', 'width': 1},
                            'left': {'style': 'SOLID', 'width': 1},
                            'right': {'style': 'SOLID', 'width': 1},
                            'innerHorizontal': {'style': 'SOLID', 'width': 1},
                            'innerVertical': {'style': 'SOLID', 'width': 1}
                        }
                    },
                    # Kolonnalarni avtomatik o'lcham
                    {
                        'autoResizeDimensions': {
                            'dimensions': {
                                'sheetId': sheet_id,
                                'dimension': 'COLUMNS',
                                'startIndex': 0,
                                'endIndex': len(headers)
                            }
                        }
                    },
                    # "Qabul qilindi" kolonnasiga checkbox qo'shish
                    {
                        'repeatCell': {
                            'range': {
                                'sheetId': sheet_id,
                                'startRowIndex': 1,
                                'endRowIndex': 1000,
                                'startColumnIndex': headers.index("Qabul qilindi"),
                                'endColumnIndex': headers.index("Qabul qilindi") + 1
                            },
                            'cell': {
                                'dataValidation': {
                                    'condition': {'type': 'BOOLEAN'}
                                }
                            },
                            'fields': 'dataValidation'
                        }
                    }
                ]
                
                sheets.batchUpdate(spreadsheetId=SHEET_ID, body={'requests': requests}).execute()
                logger.info(f"Sheet '{SHEET_TAB_NAME}' created and formatted successfully")

        except Exception as e:
            logger.error(f"Error creating sheet: {str(e)}")
            return False

        logger.info("Database connected successfully")
        return True

    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        return False



async def aiogram_on_startup_polling(dispatcher: Dispatcher, bot: Bot) -> None:
    from utils.set_bot_commands import set_default_commands
    from utils.notify_admins import on_startup_notify

    logger.info("Database connected")
    await database_connected()

    logger.info("Starting polling")
    await bot.delete_webhook(drop_pending_updates=True)
    await setup_aiogram(bot=bot, dispatcher=dispatcher)
    await on_startup_notify(bot=bot)
    await set_default_commands(bot=bot)


async def aiogram_on_shutdown_polling(dispatcher: Dispatcher, bot: Bot):
    logger.info("Stopping polling")
    await bot.session.close()
    await dispatcher.storage.close()


def main():
    """CONFIG"""
    from data.config import BOT_TOKEN
    from aiogram.enums import ParseMode
    from aiogram.fsm.storage.memory import MemoryStorage
    from aiogram.client.default import DefaultBotProperties


    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    storage = MemoryStorage()
    dispatcher = Dispatcher(storage=storage)

    dispatcher.startup.register(aiogram_on_startup_polling)
    dispatcher.shutdown.register(aiogram_on_shutdown_polling)
    asyncio.run(dispatcher.start_polling(bot, close_bot_session=True))
    # allowed_updates=['message', 'chat_member']


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Bot stopped!")
