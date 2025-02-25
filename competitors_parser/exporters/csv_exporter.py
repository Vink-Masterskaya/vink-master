import csv
from typing import Dict, Any
from .base import BaseExporter


class CSVExporter(BaseExporter):
    """Унифицированный CSV экспортер для всех пауков"""

    def open_spider(self, spider):
        """Инициализация экспортера при старте паука"""
        filename = self._get_filename(spider.name, 'csv')
        self.files[spider] = open(filename, 'w', newline='', encoding='utf-8')

        fieldnames = [
            'category',
            'product_code',
            'name',
            'price',
            'stock',
            'quantity',
            'currency',
            'unit',
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
        self.logger.info(f"Начало записи в файл: {filename}")

    def process_item(self, item: Dict[str, Any], spider) -> Dict[str, Any]:
        """Обработка и запись item в CSV файл"""
        try:
            # Создаем плоскую структуру для CSV
            flat_items = self._flatten_item(item)
            for flat_item in flat_items:
                self.exporters[spider].writerow(flat_item)

        except Exception as e:
            self.logger.error(f"Ошибка при записи в CSV: {str(e)}")

        return item

    def _flatten_item(self, item: Dict[str, Any]) -> list:
        """Преобразование вложенной структуры stocks в плоскую для CSV"""
        flat_items = []

        # Подготавливаем базовый item
        base_item = {
            'category': item.get('category', ''),
            'product_code': item.get('product_code', ''),
            'name': item.get('name', ''),
            'price': item.get('price', 0.0),
            'currency': item.get('currency', 'RUB'),
            'unit': self._format_unit(item.get('unit', 'шт')),
            'weight': item.get('weight', ''),
            'length': item.get('length', ''),
            'width': item.get('width', ''),
            'height': item.get('height', ''),
            'url': item.get('url', '')
        }

        # Получаем информацию о складах
        stocks = item.get('stocks', [])

        # Если нет информации о складах,
        # создаем одну запись с пустыми значениями
        if not stocks:
            flat_item = base_item.copy()
            flat_item.update({
                'stock': 'Основной',
                'quantity': 0
            })
            flat_items.append(flat_item)
        else:
            # Если есть информация о складах,
            # создаем отдельную запись для каждого склада
            for stock in stocks:
                flat_item = base_item.copy()
                flat_item.update({
                    'stock': stock.get('stock', 'Основной'),
                    'quantity': stock.get('quantity', 0)
                })
                flat_items.append(flat_item)

        return flat_items

    def _format_unit(self, unit):
        """Форматирование единицы измерения для CSV"""
        if isinstance(unit, list):
            return '; '.join(unit)
        return unit
