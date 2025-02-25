from scrapy import Spider
from datetime import datetime
from typing import Optional


class BaseCompetitorSpider(Spider):
    """Базовый класс для пауков парсинга конкурентов"""

    # Общие настройки для всех пауков
    custom_settings = {
        'CONCURRENT_REQUESTS': 16,
        'DOWNLOAD_DELAY': 1,
        'COOKIES_ENABLED': False,
        'USER_AGENT': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        )
    }

    # Ключевые слова для цен по запросу
    PRICE_REQUEST_KEYWORDS = [
        "по запросу", "по заказу", "звоните", "уточняйте",
        "договорная", "нет в наличии", "недоступно"
    ]

    def __init__(self, *args, **kwargs):
        """Инициализация паука"""
        super().__init__(*args, **kwargs)
        self.start_time = datetime.now()
        self.logger.info(f"Starting spider: {self.name}")

    def extract_price(self, price_text: Optional[str]) -> float:
        """
        Извлечение цены из текста.
        Если цена указана как "По запросу" или похожим образом,
        возвращает 0.0

        Args:
            price_text: Текст, содержащий цену

        Returns:
            float: Извлеченная цена или 0.0 для цены по запросу
        """
        if not price_text:
            return 0.0

        # Проверяем наличие ключевых слов для цены по запросу
        price_text_lower = price_text.lower()
        for keyword in self.PRICE_REQUEST_KEYWORDS:
            if keyword in price_text_lower:
                self.logger.info(f"Price on request: {price_text}")
                return 0.0

        try:
            # Очищаем от всего кроме цифр, точки и запятой
            clean_price = ''.join(
                c for c in price_text if c.isdigit() or c in '.,'
            )
            # Заменяем запятую на точку
            clean_price = clean_price.replace(',', '.')
            # Проверяем не пустая ли строка
            if not clean_price:
                return 0.0
            return float(clean_price)
        except (ValueError, TypeError):
            self.logger.warning(f"Could not parse price: {price_text}")
            return 0.0

    def extract_stock(self, value: Optional[str]) -> int:
        """Извлечение количества товара на складе"""
        if not value:
            return 0
        try:
            # Извлекаем только числа
            clean_value = ''.join(c for c in value if c.isdigit())
            return int(clean_value) if clean_value else 0
        except (ValueError, TypeError):
            self.logger.warning(
                f"Не удалось преобразовать количество: {value}"
            )
            return 0

    def clean_text(self, text: Optional[str]) -> str:
        """Очистка текста от лишних пробелов и переносов строк"""
        if not text:
            return ""

        # Удаляем лишние пробелы и переносы строк
        text = " ".join(text.strip().split())

        return text

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
