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
                f'Got error {response.status} on {request.url}'
            )
            # Логируем дополнительную информацию при 403 ошибке
            if response.status == 403:
                spider.logger.error(
                    f'Возможно, сайт заблокировал доступ. '
                    f'Headers: {request.headers}'
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
