# competitors_parser/exporters/json_exporter.py
import json
from typing import Dict, Any
from .base import BaseExporter


class FullFormatJSONExporter(BaseExporter):
    """Экспортер для полного формата данных (Fabreex)"""

    def open_spider(self, spider):
        if spider.name != 'fabreex':
            return
        self.items = []
        self.logger.info("Инициализация JSON экспортера для Fabreex")

    def process_item(self, item: Dict[str, Any], spider) -> Dict[str, Any]:
        if spider.name != 'fabreex':
            return item

        self.items.append(item)
        return item

    def close_spider(self, spider):
        if spider.name != 'fabreex':
            return

        filename = self._get_filename(spider.name, 'json')
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.items, f, ensure_ascii=False, indent=2)
        self.logger.info(f"Файл {filename} успешно сохранен")


class SimpleFormatJSONExporter(BaseExporter):
    """Экспортер для упрощенного формата данных"""

    def open_spider(self, spider):
        if spider.name == 'fabreex':
            return
        self.items = []
        self.logger.info(f"Инициализация JSON экспортера для {spider.name}")

    def process_item(self, item: Dict[str, Any], spider) -> Dict[str, Any]:
        if spider.name == 'fabreex':
            return item

        self.items.append(item)
        return item

    def close_spider(self, spider):
        if spider.name == 'fabreex':
            return

        filename = self._get_filename(spider.name, 'json')
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.items, f, ensure_ascii=False, indent=2)
        self.logger.info(f"Файл {filename} успешно сохранен")
