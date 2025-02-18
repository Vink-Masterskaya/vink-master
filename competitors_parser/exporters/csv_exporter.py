# competitors_parser/exporters/csv_exporter.py
import csv
from typing import Dict, Any
from .base import BaseExporter


class FullFormatCSVExporter(BaseExporter):
    def open_spider(self, spider):
        if spider.name != 'fabreex':
            return

        filename = self._get_filename(spider.name, 'csv')
        self.files[spider] = open(filename, 'w', newline='', encoding='utf-8')
        self.exporters[spider] = csv.DictWriter(
            self.files[spider],
            fieldnames=[
                'product_code',
                'name',
                'price',
                'stock',
                'quantity',
                'unit',
                'currency',
                'category',
                'url',
                'weight',
                'length',
                'width',
                'height'
            ],
            delimiter=';'
        )
        self.exporters[spider].writeheader()
        self.logger.info(f"Начало записи в файл: {filename}")

    def process_item(self, item: Dict[str, Any], spider) -> Dict[str, Any]:
        if spider.name != 'fabreex':
            return item

        try:
            # Преобразуем stocks в плоскую структуру
            flat_item = item.copy()
            if 'stocks' in flat_item:
                stocks = flat_item.pop('stocks')
                for stock_info in stocks:
                    flat_item.update({
                        'stock': stock_info['stock'],
                        'quantity': stock_info['quantity'],
                        'price': stock_info['price']
                    })
                    self.exporters[spider].writerow(flat_item)
            else:
                # Для обратной совместимости
                flat_item['quantity'] = flat_item.get('stock', 0)
                self.exporters[spider].writerow(flat_item)
        except Exception as e:
            self.logger.error(f"Ошибка при записи в CSV: {str(e)}")
        return item


class SimpleFormatCSVExporter(BaseExporter):
    """Экспортер для упрощенного формата данных"""

    def open_spider(self, spider):
        if spider.name == 'fabreex':
            return

        filename = self._get_filename(spider.name, 'csv')
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

    def process_item(self, item: Dict[str, Any], spider) -> Dict[str, Any]:
        if spider.name == 'fabreex':
            return item

        try:
            self.exporters[spider].writerow(item)
        except Exception as e:
            self.logger.error(f"Ошибка при записи в CSV: {str(e)}")
        return item
