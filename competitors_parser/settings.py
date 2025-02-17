BOT_NAME = 'competitors_parser'

SPIDER_MODULES = ['competitors_parser.spiders']
NEWSPIDER_MODULE = 'competitors_parser.spiders'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Configure maximum concurrent requests performing at the same time to the same domain
CONCURRENT_REQUESTS = 16
CONCURRENT_REQUESTS_PER_DOMAIN = 8

# Configure a delay for requests for the same website
DOWNLOAD_DELAY = 1

# Disable cookies (enabled by default)
COOKIES_ENABLED = False

# Configure item pipelines
ITEM_PIPELINES = {
    'competitors_parser.pipelines.validation.ValidationPipeline': 300,
    'competitors_parser.pipelines.csv_export.FullFormatCSVPipeline': 400,
    'competitors_parser.pipelines.csv_export.SimpleFormatCSVPipeline': 401,
}

# Enable and configure the AutoThrottle extension
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 5
AUTOTHROTTLE_MAX_DELAY = 60
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0

# Enable showing throttling stats for every response received
AUTOTHROTTLE_DEBUG = False

# Configure logging
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s [%(name)s] %(levelname)s: %(message)s'
LOG_FILE = 'logs/parser.log'

# Retry settings
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 429]
RETRY_PRIORITY_ADJUST = -1

# Middleware settings
DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': None,
    'competitors_parser.middlewares.RetryMiddleware': 550,
    'competitors_parser.middlewares.ErrorHandlerMiddleware': 560,
}

# Export settings
FEED_FORMAT = 'json'
FEED_URI = 'data/processed/%(name)s/%(time)s.json'
FEED_EXPORT_ENCODING = 'utf-8'

# CSV Export settings
CSV_EXPORT = {
    'ENCODING': 'utf-8',
    'DELIMITER': ';',
    'DIRECTORY': 'data/processed'
}

# Default headers
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ru,en-US;q=0.7,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}

# Cache settings for development
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 0
HTTPCACHE_DIR = 'httpcache'
HTTPCACHE_IGNORE_HTTP_CODES = []
HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'

# Redirects
REDIRECT_ENABLED = True
REDIRECT_MAX_TIMES = 3
