import csv
import json
from typing import Any, Dict

from .base import BaseExporter


class PlaywrightCSVExporter(BaseExporter):
    """CSV экспортер специально для пауков, использующих Playwright."""

    def open_spider(self, spider):
        """Инициализация экспортера при старте паука."""
        filename = self._get_filename(spider.name, 'csv')
        self.files[spider] = open(filename, 'w', newline='', encoding='utf-8')

        fieldnames = [
            'category',
            'product_code',
            'name',
            'price',
            'stocks',
            'unit',
            'currency',
            'url'
        ]

        self.exporters[spider] = csv.DictWriter(
            self.files[spider],
            fieldnames=fieldnames,
            delimiter=';'
        )
        self.exporters[spider].writeheader()
        self.logger.info(f"Начало записи в CSV файл: {filename}")

    def process_item(self, item: Dict[str, Any], spider) -> Dict[str, Any]:
        """Обработка и запись item в CSV файл."""
        try:
            csv_item = self._prepare_csv_item(item)

            self.exporters[spider].writerow(csv_item)
            self.logger.info(f"Товар {item.get('name', '')} записан в CSV")

        except Exception as e:
            self.logger.error(f"Ошибка при записи в CSV: {str(e)}")

        return item

    def _prepare_csv_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Подготовка item для записи в CSV файл."""
        csv_item = {}

        csv_item['category'] = item.get('category', '')
        csv_item['product_code'] = item.get('product_code', '')
        csv_item['name'] = item.get('name', '')
        csv_item['price'] = item.get('price', 0.0)
        csv_item['unit'] = self._format_unit(item.get('unit', 'шт'))
        csv_item['currency'] = item.get('currency', 'RUB')
        csv_item['url'] = item.get('url', '')

        stocks = item.get('stocks', [])
        if stocks:
            csv_item['stocks'] = json.dumps(stocks, ensure_ascii=False)
        else:
            csv_item['stocks'] = '[]'

        return csv_item

    def _format_unit(self, unit):
        """Форматирование единицы измерения."""
        if isinstance(unit, list):
            return '; '.join(unit)
        return str(unit)
