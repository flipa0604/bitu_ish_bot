from environs import Env

# environs kutubxonasidan foydalanish
env = Env()
env.read_env()

# .env fayl ichidan quyidagilarni o'qiymiz
BOT_TOKEN = env.str("BOT_TOKEN")  # Bot Token
ADMINS = env.list("ADMINS")  # adminlar ro'yxati


BACKEND_HOST = env.str("BACKEND_HOST", "http://localhost:8000")

SERVICE_ACCOUNT = {
    "type": env.str("TYPE"),
    "project_id": env.str("PROJECT_ID"),
    "private_key_id": env.str("PRIVATE_KEY_ID"),
    "private_key": env.str("PRIVATE_KEY"),
    "client_email": env.str("CLIENT_EMAIL"),
    "client_id": env.str("CLIENT_ID"),
    "auth_uri": env.str("AUTH_URI"),
    "token_uri": env.str("TOKEN_URI"),
    "auth_provider_x509_cert_url": env.str("AUTH_PROVIDER_X509_CERT_URL"),
    "client_x509_cert_url": env.str("CLIENT_X509_CERT_URL")
}
