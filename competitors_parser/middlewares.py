from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.utils.response import response_status_message
import time


class RetryMiddleware(RetryMiddleware):
    def __init__(self, settings):
        super().__init__(settings)
        self.priority_adjust = settings.getint('RETRY_PRIORITY_ADJUST')

    def process_response(self, request, response, spider):
        if request.meta.get('dont_retry', False):
            return response
        if response.status in self.retry_http_codes:
            self._retry(request, response.status, spider)
            return self._retry(request, response.status, spider) or response
        return response

    def process_exception(self, request, exception, spider):
        if isinstance(exception, self.EXCEPTIONS_TO_RETRY) and not request.meta.get('dont_retry', False):
            time.sleep(self.settings.getint('DOWNLOAD_DELAY', 0))
            return self._retry(request, exception, spider)


class ErrorHandlerMiddleware:
    def __init__(self, crawler):
        self.crawler = crawler

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def process_response(self, request, response, spider):
        if response.status >= 400:
            spider.logger.error(
                f"Got error {response.status} on {request.url}"
            )
        return response

    def process_exception(self, request, exception, spider):
        spider.logger.error(
            f'Failed to process {request.url}: {exception}'
        )
        return None
