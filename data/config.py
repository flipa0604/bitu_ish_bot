from environs import Env

# environs kutubxonasidan foydalanish
env = Env()
env.read_env()

# .env fayl ichidan quyidagilarni o'qiymiz
BOT_TOKEN = env.str("BOT_TOKEN")  # Bot Token
ADMINS = env.list("ADMINS")  # adminlar ro'yxati


BACKEND_HOST = env.str("BACKEND_HOST", "http://localhost:8000")

# Google Sheets ID (URL'dagi /d/ va /edit orasidagi qism)
SHEET_ID = env.str("SHEET_ID")
SHEET_TAB_NAME = env.str("SHEET_TAB_NAME", "Topshirganlar")
SERVICE_ACCOUNT_FILE = env.str("SERVICE_ACCOUNT_FILE", "service_account.json")

# SERVICE_ACCOUNT — endi kodda ishlatilmaydi. service_account.json fayli to'g'ridan-to'g'ri o'qiladi.
