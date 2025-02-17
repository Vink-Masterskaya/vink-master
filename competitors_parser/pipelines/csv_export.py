import csv
from datetime import datetime
import logging
from pathlib import Path


class BaseCSVPipeline:
    """Базовый класс для CSV экспорта"""

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


class FullFormatCSVPipeline(BaseCSVPipeline):
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
            ],
            delimiter=';'
        )
        self.exporters[spider].writeheader()
        self.logger.info(f"Начало записи в файл: {filename}")

    def process_item(self, item, spider):
        if spider.name != 'fabreex':
            return item

        try:
            self.exporters[spider].writerow(item)
        except Exception as e:
            self.logger.error(f"Ошибка при записи в CSV: {str(e)}")
        return item


class SimpleFormatCSVPipeline(BaseCSVPipeline):
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
            ],
            delimiter=';'
        )
        self.exporters[spider].writeheader()
        self.logger.info(f"Начало записи в файл: {filename}")

    def process_item(self, item, spider):
        if spider.name == 'fabreex':
            return item

        try:
            self.exporters[spider].writerow(item)
        except Exception as e:
            self.logger.error(f"Ошибка при записи в CSV: {str(e)}")
        return item
