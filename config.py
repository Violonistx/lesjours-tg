from dotenv import load_dotenv
import os

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
API_BASE_URL   = os.getenv('API_BASE_URL', 'https://les-jours.ru')

if not TELEGRAM_TOKEN:
    raise RuntimeError('TELEGRAM_TOKEN не задан в окружении')
