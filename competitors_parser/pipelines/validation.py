from scrapy.exceptions import DropItem


class ValidationPipeline:
    def process_item(self, item, spider):
        """
        Валидация данных в зависимости от типа парсера
        """
        if spider.name == 'fabreex':
            return self._validate_fabreex_item(item, spider)
        else:
            return self._validate_simple_item(item, spider)

    def _validate_fabreex_item(self, item, spider):
        """Валидация для полного формата данных Fabreex"""
        # Проверяем только наличие имени, остальные поля опциональны
        if not item.get('name'):
            spider.logger.warning("Отсутствует название товара")
            raise DropItem("Отсутствует название товара")

        # Проверяем типы данных
        if 'price' in item and item['price']:
            try:
                item['price'] = float(item['price'])
            except (ValueError, TypeError):
                spider.logger.warning(f"Неверный формат цены: {item['price']}")
                item['price'] = 0.0

        if 'stock' in item and item['stock']:
            try:
                item['stock'] = int(item['stock'])
            except (ValueError, TypeError):
                spider.logger.warning(
                    f"Неверный формат количества: {item['stock']}"
                )
                item['stock'] = 0

        # Устанавливаем значения по умолчанию
        item.setdefault('product_code', '')
        item.setdefault('price', 0.0)
        item.setdefault('stock', 0)
        item.setdefault('unit', 'шт.')
        item.setdefault('currency', 'RUB')
        item.setdefault('category', '')
        item.setdefault('url', '')

        return item

    def _validate_simple_item(self, item, spider):
        """Валидация для упрощенного формата данных"""
        # Проверяем только имя и город
        if not item.get('name'):
            spider.logger.warning("Отсутствует название товара")
            raise DropItem("Отсутствует название товара")

        if not item.get('city'):
            spider.logger.warning("Отсутствует город")
            raise DropItem("Отсутствует город")

        # Проверяем количество
        if 'stock' in item and item['stock']:
            try:
                item['stock'] = int(item['stock'])
            except (ValueError, TypeError):
                spider.logger.warning(
                    f"Неверный формат количества: {item['stock']}"
                )
                item['stock'] = 0

        # Устанавливаем значения по умолчанию
        item.setdefault('stock', 0)
        item.setdefault('category', '')
        item.setdefault('url', '')

        return item
