from scrapy import Spider
from typing import Dict, Any, Optional
import logging
from datetime import datetime

class BaseCompetitorSpider(Spider):
    custom_settings = {
        'CONCURRENT_REQUESTS': 16,
        'DOWNLOAD_DELAY': 1,
        'ITEM_PIPELINES': {
            'src.pipelines.validation.ValidationPipeline': 300,
            'src.pipelines.json_export.JSONExportPipeline': 400,
        }
    }

# @property
# def logger(self):
#     return logging.getLogger('my_logger')


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
#        logger = logging.getLogger(__name__)
        self.start_time = datetime.now()

    def extract_price(self, value: Optional[str]) -> float:
        """Извлечение и очистка цены"""
        if not value:
            return 0.0
        try:
            clean_value = ''.join(c for c in value if c.isdigit() or c in '.,')
            return float(clean_value.replace(',', '.'))
        except (ValueError, TypeError):
            self.logger.warning(f"Не удалось преобразовать цену: {value}")
            return 0.0

    def extract_stock(self, value: Optional[str]) -> int:
        """Извлечение количества товара"""
        if not value:
            return 0
        try:
            clean_value = ''.join(c for c in value if c.isdigit())
            return int(clean_value) if clean_value else 0
        except (ValueError, TypeError):
            self.logger.warning(f"Не удалось преобразовать количество: {value}")
            return 0
