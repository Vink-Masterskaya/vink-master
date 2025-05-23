import json
from collections import OrderedDict
from typing import Any, Dict

from .base import BaseExporter


class JSONExporter(BaseExporter):
    """Унифицированный JSON экспортер для всех пауков."""

    def open_spider(self, spider):
        """Инициализация экспортера при старте паука."""
        self.items = []
        self.logger.info(f'Инициализация JSON экспортера для {spider.name}')

    def process_item(self, item: Dict[str, Any], spider) -> Dict[str, Any]:
        """Обработка и сохранение item для последующей записи в JSON."""
        try:
            ordered_item = OrderedDict()
            ordered_item['category'] = item.get('category', '')
            ordered_item['product_code'] = item.get('product_code', '')
            ordered_item['name'] = item.get('name', '')
            ordered_item['stocks'] = item.get('stocks', [])
            ordered_item['unit'] = item.get('unit', '')
            ordered_item['currency'] = item.get('currency', 'RUB')
            ordered_item['weight'] = item.get('weight', None)
            ordered_item['length'] = item.get('length', None)
            ordered_item['width'] = item.get('width', None)
            ordered_item['height'] = item.get('height', None)
            ordered_item['url'] = item.get('url', '')

            self.items.append(ordered_item)
            self.logger.info(
                f'Товар {item.get("name", "")} добавлен в JSON список'
                )

        except Exception as e:
            self.logger.error(f'Ошибка при обработке item для JSON: {str(e)}')

        return item

    def close_spider(self, spider):
        """Запись JSON файла при завершении работы паука."""
        try:
            filename = self._get_filename(spider.name, 'json')
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.items, f, ensure_ascii=False, indent=2)
            self.logger.info(
                f'Файл {filename} успешно сохранен. Всего товаров: {
                    len(self.items)
                    }'
                )

        except Exception as e:
            self.logger.error(f'Ошибка при сохранении JSON: {str(e)}')
