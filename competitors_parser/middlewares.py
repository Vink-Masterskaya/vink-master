from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.utils.response import response_status_message
import time


class RetryMiddleware(RetryMiddleware):
    def __init__(self, settings):
        super().__init__(settings)
        self.priority_adjust = settings.getint('RETRY_PRIORITY_ADJUST')

    def process_response(self, request, response, spider):
        """
        Обработка ответа сервера.
        Если получен статус из списка RETRY_HTTP_CODES, пытаемся повторить запрос.
        """
        if request.meta.get('dont_retry', False):
            return response

        if response.status in self.retry_http_codes:
            self._retry(request, response.status, spider)
            return self._retry(request, response.status, spider) or response

        return response

    def process_exception(self, request, exception, spider):
        """
        Обработка исключений при запросе.
        Если исключение в списке EXCEPTIONS_TO_RETRY, пытаемся повторить запрос.
        """
        if isinstance(exception, self.EXCEPTIONS_TO_RETRY) and not request.meta.get('dont_retry', False):
            time.sleep(self.settings.getint('DOWNLOAD_DELAY', 0))
            return self._retry(request, exception, spider)


class ErrorHandlerMiddleware:
    """Middleware для обработки и логирования ошибок"""

    def __init__(self, crawler):
        self.crawler = crawler

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def process_response(self, request, response, spider):
        """Обработка ответов с ошибками"""
        if response.status >= 400:
            spider.logger.error(
                f"Got error {response.status} on {request.url}"
            )
            # Логируем дополнительную информацию при 403 ошибке
            if response.status == 403:
                spider.logger.error(
                    f"Возможно, сайт заблокировал доступ. Headers: {request.headers}"
                )
        return response

    def process_exception(self, request, exception, spider):
        """Обработка исключений при запросе"""
        spider.logger.error(
            f'Failed to process {request.url}: {str(exception)}'
        )
        # Логируем дополнительную информацию о запросе
        spider.logger.error(
            f'Request details: method={request.method}, '
            f'headers={request.headers}, meta={request.meta}'
        )
        return None

    def process_spider_exception(self, response, exception, spider):
        """Обработка исключений в пауке"""
        spider.logger.error(
            f'Spider error processing {response.url}: {str(exception)}'
        )
        return None
