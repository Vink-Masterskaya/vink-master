from scrapy.spiders import CrawlSpider
from datetime import datetime
import re
from typing import Optional, Dict, Any


class BaseCompetitorSpider(CrawlSpider):
    """Базовый класс для пауков-краулеров парсинга конкурентов"""

    # Общие настройки для всех пауков
    custom_settings = {
        'CONCURRENT_REQUESTS': 16,
        'DOWNLOAD_DELAY': 1,
        'COOKIES_ENABLED': False,
        'USER_AGENT': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    }

    def __init__(self, *args, **kwargs):
        """Инициализация паука"""
        super().__init__(*args, **kwargs)
        self.start_time = datetime.now()

    def extract_price(self, price_text: Optional[str]) -> float:
        """Извлечение цены из текста"""
        if not price_text:
            return 0.0
        try:
            # Очищаем от всего кроме цифр, точки и запятой
            clean_price = ''.join(
                c for c in price_text if c.isdigit() or c in '.,'
            )
            # Заменяем запятую на точку
            clean_price = clean_price.replace(',', '.')
            return float(clean_price)
        except (ValueError, TypeError):
            self.logger.warning(f"Could not parse price: {price_text}")
            return 0.0

    def extract_stock(self, value: Optional[str]) -> float:
        """Извлечение количества товара из текста"""
        if not value:
            return 0
        try:
            # Извлекаем числа, включая десятичные
            numbers = re.findall(r'\d+(?:\.\d+)?', str(value))
            return float(numbers[0]) if numbers else 0
        except (ValueError, IndexError):
            self.logger.warning(f"Не удалось извлечь количество из: {value}")
            return 0

    def clean_text(self, text: Optional[str]) -> str:
        """Очистка текста от лишних пробелов и переносов строк"""
        if not text:
            return ""
        return " ".join(text.strip().split())

    def get_category_from_url(self, url: str) -> str:
        """Получение категории из URL"""
        parts = url.split('/')[3:-2]  # Пропускаем домен и последние части
        return ' / '.join(
            part.replace('-', ' ').title()
            for part in parts
            if part and part not in ['catalog', 'product']
        )

    def create_product_code(self, name: str, **params: Dict[str, Any]) -> str:
        """
        Создание артикула товара из названия и дополнительных параметров

        Args:
            name (str): Название товара
            **params: Дополнительные параметры (например, width='100', density='200')
        """
        parts = [self.clean_text(name)]
        parts.extend(str(value) for value in params.values() if value)
        product_code = '_'.join(parts)
        return re.sub(r'[^\w\-]', '_', product_code)

    def get_full_url(self, url: Optional[str]) -> Optional[str]:
        """Получение полного URL"""
        if not url:
            return None
        if url.startswith('http'):
            return url
        return (f"https://{self.allowed_domains[0]}"
                f"{url if url.startswith('/') else '/' + url}")

    def closed(self, reason: str) -> None:
        """Вызывается при завершении работы паука"""
        duration = datetime.now() - self.start_time
        self.logger.info(
            f"Паук {self.name} завершил работу. "
            f"Причина: {reason}. Время работы: {duration}"
        )
