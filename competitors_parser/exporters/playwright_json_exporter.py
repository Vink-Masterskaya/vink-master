import json
from typing import Dict, Any
from collections import OrderedDict
from .base import BaseExporter


class PlaywrightJSONExporter(BaseExporter):
    """JSON экспортер специально для пауков, использующих Playwright"""

    def open_spider(self, spider):
        """Инициализация экспортера при старте паука"""
        self.items = []
        self.logger.info(f"Инициализация JSON экспортера для {spider.name}")

    def process_item(self, item: Dict[str, Any], spider) -> Dict[str, Any]:
        """Обработка и сохранение item для последующей записи в JSON"""
        try:
            # Создаем OrderedDict для сохранения порядка полей
            ordered_item = OrderedDict()
            ordered_item['category'] = item.get('category', '')
            ordered_item['product_code'] = item.get('product_code', '')
            ordered_item['name'] = item.get('name', '')
            ordered_item['price'] = item.get('price', 0.0)

            # Обработка складов - проверка наличия и корректное форматирование
            stocks = item.get('stocks', [])
            ordered_item['stocks'] = stocks

            ordered_item['unit'] = item.get('unit', 'шт')
            ordered_item['currency'] = item.get('currency', 'RUB')
            ordered_item['url'] = item.get('url', '')

            # Добавляем item в список
            self.items.append(ordered_item)
            self.logger.info(
                f"Товар {item.get('name', '')} добавлен в список для JSON"
                )

        except Exception as e:
            self.logger.error(f"Ошибка при обработке item для JSON: {str(e)}")

        return item

    def close_spider(self, spider):
        """Запись JSON файла при завершении работы паука"""
        try:
            # Формируем имя файла и сохраняем данные
            filename = self._get_filename(spider.name, 'json')
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.items, f, ensure_ascii=False, indent=2)

            self.logger.info(
                f"JSON файл {filename} успешно сохранен. "
                f"Всего товаров: {len(self.items)}"
                )

        except Exception as e:
            self.logger.error(f"Ошибка при сохранении JSON: {str(e)}")
