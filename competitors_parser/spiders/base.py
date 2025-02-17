from typing import Optional
from datetime import datetime
from scrapy import Spider, Request
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError, TimeoutError
from urllib.parse import urljoin


class BaseCompetitorSpider(Spider):
    """Базовый класс для пауков парсинга конкурентов"""

    custom_settings = {
        'CONCURRENT_REQUESTS': 16,
        'DOWNLOAD_DELAY': 1,
        'COOKIES_ENABLED': False,
        'USER_AGENT': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/91.0.4472.124 Safari/537.36'
        )
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_time = datetime.now()

    def start_requests(self):
        """Метод генерации начальных запросов"""
        for url in self.start_urls:
            yield self.make_request(url)

    def make_request(self, url, callback=None, **kwargs):
        """Создание запроса с базовыми параметрами"""
        if not callback:
            callback = self.parse
        return Request(
            url=url,
            callback=callback,
            dont_filter=kwargs.get('dont_filter', False),
            errback=self.errback_httpbin,
            meta=kwargs.get('meta', {})
        )

    def errback_httpbin(self, failure):
        """Обработка ошибок при запросах"""
        self.logger.error(f'Request failed: {failure.request.url}')
        if failure.check(HttpError):
            response = failure.value.response
            self.logger.error(f'HttpError on {response.url}')
        elif failure.check(DNSLookupError):
            request = failure.request
            self.logger.error(f'DNSLookupError on {request.url}')
        elif failure.check(TimeoutError):
            request = failure.request
            self.logger.error(f'TimeoutError on {request.url}')

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
        return " ".join(text.strip().split())

    def get_full_url(self, url: str) -> str:
        """Получение полного URL"""
        return urljoin(self.start_urls[0], url)

    def closed(self, reason):
        """Вызывается при завершении работы паука"""
        duration = datetime.now() - self.start_time
        self.logger.info(
            f"Паук {self.name} завершил работу. "
            f"Причина: {reason}. Время работы: {duration}"
        )
