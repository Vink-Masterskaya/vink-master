from scrapy.exceptions import DropItem


class ValidationPipeline:
    """Pipeline для валидации данных"""

    required_fields = {'product_code', 'name', 'price'}

    def process_item(self, item, spider):
        # Проверка обязательных полей
        for field in self.required_fields:
            if not item.get(field):
                spider.logger.warning(f"Отсутствует обязательное поле {field}")
                raise DropItem(f"Отсутствует обязательное поле {field}")

        # Валидация цены
        try:
            price = float(item['price'])
            if price < 0:
                raise DropItem(f"Недопустимая цена: {price}")
            item['price'] = price
        except (ValueError, TypeError):
            spider.logger.warning(f"Неверный формат цены: {item['price']}")
            raise DropItem(f"Неверный формат цены: {item['price']}")

        # Валидация количества
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
        for field in ['product_code', 'name', 'unit', 'currency']:
            if field in item:
                item[field] = str(item[field]).strip()

        return item
