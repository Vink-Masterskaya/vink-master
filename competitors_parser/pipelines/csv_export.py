import csv
from datetime import datetime
import logging
from pathlib import Path


class BaseCSVExportPipeline:
    """Базовый класс для экспорта в CSV"""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.files = {}
        self.exporters = {}

    def close_spider(self, spider):
        """Завершение работы при остановке паука"""
        if spider in self.files:
            filename = self.files[spider].name
            self.files[spider].close()
            self.logger.info(f"Файл {filename} успешно сохранен")


class FullFormatCSVPipeline(BaseCSVExportPipeline):
    """Пайплайн для полного формата данных (Fabreex)"""

    def open_spider(self, spider):
        if spider.name != 'fabreex':
            return

        export_dir = Path(f"data/processed/{spider.name}")
        export_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = export_dir / f"{spider.name}_{timestamp}.csv"

        self.files[spider] = open(filename, 'w', newline='', encoding='utf-8')
        self.exporters[spider] = csv.DictWriter(
            self.files[spider],
            fieldnames=[
                'product_code',
                'name',
                'price',
                'stock',
                'unit',
                'currency',
                'category',
                'url'
            ]
        )
        self.exporters[spider].writeheader()
        self.logger.info(f"Начало записи в файл: {filename}")

    def process_item(self, item, spider):
        if spider.name != 'fabreex':
            return item

        try:
            row = {
                'product_code': item.get('product_code', ''),
                'name': item.get('name', ''),
                'price': item.get('price', 0.0),
                'stock': item.get('stock', 0),
                'unit': item.get('unit', 'шт.'),
                'currency': item.get('currency', 'RUB'),
                'category': item.get('category', ''),
                'url': item.get('url', '')
            }
            self.exporters[spider].writerow(row)

        except Exception as e:
            self.logger.error(f"Ошибка при записи в CSV: {str(e)}")

        return item


class SimpleFormatCSVPipeline(BaseCSVExportPipeline):
    """Пайплайн для упрощенного формата данных (остальные сайты)"""

    def open_spider(self, spider):
        if spider.name == 'fabreex':
            return

        export_dir = Path(f"data/processed/{spider.name}")
        export_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = export_dir / f"{spider.name}_{timestamp}.csv"

        self.files[spider] = open(filename, 'w', newline='', encoding='utf-8')
        self.exporters[spider] = csv.DictWriter(
            self.files[spider],
            fieldnames=[
                'category',
                'name',
                'city',
                'stock',
                'url'
            ]
        )
        self.exporters[spider].writeheader()
        self.logger.info(f"Начало записи в файл: {filename}")

    def process_item(self, item, spider):
        if spider.name == 'fabreex':
            return item

        try:
            row = {
                'category': item.get('category', ''),
                'name': item.get('name', ''),
                'city': item.get('city', ''),
                'stock': item.get('stock', 0),
                'url': item.get('url', '')
            }
            self.exporters[spider].writerow(row)

        except Exception as e:
            self.logger.error(f"Ошибка при записи в CSV: {str(e)}")

        return item
