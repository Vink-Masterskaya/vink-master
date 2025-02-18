BOT_NAME = 'competitors_parser'

SPIDER_MODULES = ['competitors_parser.spiders']
NEWSPIDER_MODULE = 'competitors_parser.spiders'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    )

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Configure maximum concurrent requests
CONCURRENT_REQUESTS = 16
CONCURRENT_REQUESTS_PER_DOMAIN = 8

# Configure a delay for requests for the same website
DOWNLOAD_DELAY = 1

# Disable cookies
COOKIES_ENABLED = False

# Configure item pipelines
ITEM_PIPELINES = {
    'competitors_parser.pipelines.validation.ValidationPipeline': 300,
    'competitors_parser.exporters.csv_exporter.FullFormatCSVExporter': 400,
    'competitors_parser.exporters.csv_exporter.SimpleFormatCSVExporter': 401,
    'competitors_parser.exporters.json_exporter.FullFormatJSONExporter': 402,
    'competitors_parser.exporters.json_exporter.SimpleFormatJSONExporter': 403,
}

# Enable and configure AutoThrottle
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 5
AUTOTHROTTLE_MAX_DELAY = 60
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
AUTOTHROTTLE_DEBUG = False

# Configure logging
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s [%(name)s] %(levelname)s: %(message)s'
LOG_FILE = 'logs/parser.log'

# Retry settings
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 429]

# Middleware settings
DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': 550,
    'competitors_parser.middlewares.ErrorHandlerMiddleware': 560,
}

# Cache settings
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 0  # Never expire
HTTPCACHE_DIR = '.scrapy/httpcache'

# CSV Export settings
CSV_EXPORT = {
    'ENCODING': 'utf-8',
    'DELIMITER': ';',
    'DIRECTORY': 'data/processed'
}
