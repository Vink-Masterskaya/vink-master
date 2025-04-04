BOT_NAME = 'competitors_parser'

SPIDER_MODULES = ['competitors_parser.spiders']
NEWSPIDER_MODULE = 'competitors_parser.spiders'

USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    )

ROBOTSTXT_OBEY = False

CONCURRENT_REQUESTS = 16
CONCURRENT_REQUESTS_PER_DOMAIN = 8

DOWNLOAD_DELAY = 1

COOKIES_ENABLED = False

ITEM_PIPELINES = {
    'competitors_parser.pipelines.validation.ValidationPipeline': 300,
    'competitors_parser.exporters.csv_exporter.CSVExporter': 400,
    'competitors_parser.exporters.json_exporter.JSONExporter': 500,
}

AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 5
AUTOTHROTTLE_MAX_DELAY = 60
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
AUTOTHROTTLE_DEBUG = False

LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s [%(name)s] %(levelname)s: %(message)s'
LOG_FILE = 'logs/parser.log'

RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 429]

DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': 550,
    'competitors_parser.middlewares.ErrorHandlerMiddleware': 560,
}

HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 0
HTTPCACHE_DIR = '.scrapy/httpcache'

CSV_EXPORT = {
    'ENCODING': 'utf-8',
    'DELIMITER': ';',
    'DIRECTORY': 'data/processed'
}
