from scrapy.exceptions import DropItem


class ValidationPipeline:
    """Pipeline для валидации данных"""

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
        required_fields = {'product_code', 'name', 'price'}

        # Проверка обязательных полей
        for field in required_fields:
            if not item.get(field):
                spider.logger.warning(f"Отсутствует обязательное поле {field}")
                raise DropItem(f"Отсутствует обязательное поле {field}")

        try:
            # Валидация цены
            price = float(item['price'])
            if price < 0:
                raise DropItem(f"Недопустимая цена: {price}")
            item['price'] = price
        except (ValueError, TypeError):
            spider.logger.warning(f"Неверный формат цены: {item['price']}")
            raise DropItem(f"Неверный формат цены: {item['price']}")

        # Валидация количества, если оно указано
        if 'stock' in item:
            try:
                stock = int(item['stock'])
                if stock < 0:
                    raise DropItem(f"Недопустимое количество: {stock}")
                item['stock'] = stock
            except (ValueError, TypeError):
                spider.logger.warning(f"Неверный формат количества: {item['stock']}")
                raise DropItem(f"Неверный формат количества: {item['stock']}")

        # Проверка и очистка строковых полей
        for field in ['product_code', 'name', 'unit', 'currency', 'category']:
            if field in item:
                item[field] = str(item[field]).strip()

        # Установка значений по умолчанию
        item.setdefault('unit', 'шт.')
        item.setdefault('currency', 'RUB')
        item.setdefault('stock', 0)

        return item

    def _validate_simple_item(self, item, spider):
        """Валидация для упрощенного формата данных"""
        required_fields = {'name', 'city'}

        # Проверка обязательных полей
        for field in required_fields:
            if not item.get(field):
                spider.logger.warning(f"Отсутствует обязательное поле {field}")
                raise DropItem(f"Отсутствует обязательное поле {field}")

        # Валидация количества
        try:
            stock = int(item.get('stock', 0))
            if stock < 0:
                raise DropItem(f"Недопустимое количество: {stock}")
            item['stock'] = stock
        except (ValueError, TypeError):
            spider.logger.warning(f"Неверный формат количества: {item['stock']}")
            raise DropItem(f"Неверный формат количества: {item['stock']}")

        # Проверка и очистка строковых полей
        for field in ['name', 'city', 'category']:
            if field in item:
                item[field] = str(item[field]).strip()

        # Установка значений по умолчанию
        item.setdefault('category', '')
        item.setdefault('stock', 0)

        return item
