from dotenv import load_dotenv
import os
from pathlib import Path

# Загружаем .env
load_dotenv()

# Базовые пути
BASE_DIR = Path(__file__).resolve().parent.parent.parent
EXPORT_DIR = BASE_DIR / 'data/exports'
LOG_DIR = BASE_DIR / 'logs'

# Настройки парсера
CONCURRENT_REQUESTS = int(os.getenv('CONCURRENT_REQUESTS', 16))
DOWNLOAD_DELAY = int(os.getenv('DOWNLOAD_DELAY', 1))
RETRY_TIMES = int(os.getenv('RETRY_TIMES', 3))

# Структура данных
REQUIRED_FIELDS = ['product_code', 'name', 'price']
OPTIONAL_FIELDS = ['stock', 'unit', 'currency']

# URLs
ZENON_URL = 'https://zenonline.ru/catalog'
REMEX_URL = 'https://www.remex.ru/catalog'
