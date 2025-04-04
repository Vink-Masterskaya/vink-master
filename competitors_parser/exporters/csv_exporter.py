import csv
import json
from typing import Any, Dict

from .base import BaseExporter


class CSVExporter(BaseExporter):
    """Унифицированный CSV экспортер для всех пауков."""

    def open_spider(self, spider):
        """Инициализация экспортера при старте паука."""
        filename = self._get_filename(spider.name, 'csv')
        self.files[spider] = open(filename, 'w', newline='', encoding='utf-8')

        fieldnames = [
            'category',
            'product_code',
            'name',
            'stocks',
            'unit',
            'currency',
            'weight',
            'length',
            'width',
            'height',
            'url'
        ]

        self.exporters[spider] = csv.DictWriter(
            self.files[spider],
            fieldnames=fieldnames,
            delimiter=';'
        )
        self.exporters[spider].writeheader()
        self.logger.info(f'Начало записи в файл CSV: {filename}')

    def process_item(self, item: Dict[str, Any], spider) -> Dict[str, Any]:
        """Обработка и запись item в CSV файл."""
        try:
            csv_item = self._format_item(item)
            self.exporters[spider].writerow(csv_item)
            self.logger.info(f'Товар {item.get("name", "")} записан в CSV')

        except Exception as e:
            self.logger.error(f'Ошибка при записи в CSV: {str(e)}')

        return item

    def _format_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Форматирование item для CSV с сохранением структуры складов."""
        csv_item = {
            'category': item.get('category', ''),
            'product_code': item.get('product_code', ''),
            'name': item.get('name', ''),
            'currency': item.get('currency', 'RUB'),
            'unit': self._format_unit(item.get('unit', 'шт')),
            'weight': item.get('weight', ''),
            'length': item.get('length', ''),
            'width': item.get('width', ''),
            'height': item.get('height', ''),
            'url': item.get('url', '')
        }

        stocks = item.get('stocks', [])
        if stocks:
            csv_item['stocks'] = json.dumps(stocks, ensure_ascii=False)
        else:
            price = item.get('price', 0.0)
            csv_item['stocks'] = json.dumps([{
                'stock': 'Основной',
                'quantity': 0,
                'price': price
            }], ensure_ascii=False)

        return csv_item

    def _format_unit(self, unit):
        """Форматирование единицы измерения для CSV."""
        if isinstance(unit, list):
            return '; '.join(unit)
        return unit
