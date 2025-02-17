import csv
import os
from datetime import datetime
import logging
from pathlib import Path


class CSVExportPipeline:
    """Пайплайн для экспорта данных в CSV"""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.files = {}
        self.exporters = {}

    def open_spider(self, spider):
        """Инициализация при старте паука"""
        # Создаем директорию для экспорта если её нет
        export_dir = Path(f"data/processed/{spider.name}")
        export_dir.mkdir(parents=True, exist_ok=True)

        # Формируем имя файла с timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = export_dir / f"{spider.name}_{timestamp}.csv"

        # Открываем файл
        self.files[spider] = open(filename, 'w', newline='', encoding='utf-8')

        # Создаем CSV writer
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
        # Записываем заголовки
        self.exporters[spider].writeheader()

        self.logger.info(f"Начало записи в файл: {filename}")

    def close_spider(self, spider):
        """Завершение работы при остановке паука"""
        if spider in self.files:
            filename = self.files[spider].name
            self.files[spider].close()
            self.logger.info(f"Файл {filename} успешно сохранен")

    def process_item(self, item, spider):
        """Обработка элемента"""
        try:
            # Подготавливаем данные для записи
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

            # Записываем строку в CSV
            self.exporters[spider].writerow(row)
            return item

        except Exception as e:
            self.logger.error(f"Ошибка при записи в CSV: {str(e)}")
            return item
