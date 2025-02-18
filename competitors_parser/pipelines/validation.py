from typing import Dict, Any, Union
import logging
from scrapy.exceptions import DropItem

# Определяем тип для числовых значений
NumberType = Union[float, int]


class ValidationPipeline:
    """Валидация данных перед сохранением"""

    def __init__(self) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)

    def process_item(self, item: Dict[str, Any], spider) -> Dict[str, Any]:
        """Валидация данных в зависимости от типа парсера"""
        if spider.name == 'fabreex':
            return self._validate_fabreex_item(item, spider)
        return self._validate_simple_item(item, spider)

    def _validate_fabreex_item(self, item: Dict[str, Any], spider) -> Dict[str, Any]:
        """Валидация для полного формата данных Fabreex"""
        if not item.get('name'):
            msg = "Missing required field: name"
            self.logger.warning(msg)
            raise DropItem(msg)

        if 'stocks' in item:
            if not isinstance(item['stocks'], list):
                self.logger.warning("Stocks must be a list")
                item['stocks'] = []
            else:
                valid_stocks = []
                for stock in item['stocks']:
                    if isinstance(stock, dict):
                        valid_stock = {
                            'stock': str(stock.get('stock', '')).strip(),
                            'quantity': self._validate_number(
                                stock.get('quantity', 0),
                                'quantity'
                            ),
                            'price': self._validate_number(
                                stock.get('price', 0.0),
                                'price',
                                float
                            )
                        }
                        valid_stocks.append(valid_stock)
                item['stocks'] = valid_stocks

        defaults = {
            'product_code': '',
            'price': 0.0,
            'unit': 'шт.',
            'currency': 'RUB',
            'category': '',
            'url': '',
            'weight': None,
            'length': None,
            'width': None,
            'height': None
        }

        for field, default in defaults.items():
            item.setdefault(field, default)

        item['price'] = self._validate_number(item['price'], 'price', float)

        return item

    def _validate_simple_item(self, item: Dict[str, Any], spider) -> Dict[str, Any]:
        """Валидация для упрощенного формата данных"""
        required_fields = ['name', 'city']
        for field in required_fields:
            if not item.get(field):
                msg = f"Missing required field: {field}"
                self.logger.warning(msg)
                raise DropItem(msg)

        defaults = {
            'stock': 0,
            'category': '',
            'url': ''
        }

        for field, default in defaults.items():
            item.setdefault(field, default)

        item['stock'] = self._validate_number(item['stock'], 'stock', int)

        return item

    def _validate_number(
        self,
        value: Any,
        field_name: str,
        number_type: type = float
    ) -> NumberType:
        """Валидация числового значения"""
        try:
            if value is None:
                return 0 if number_type is int else 0.0
            return number_type(value)
        except (ValueError, TypeError):
            self.logger.warning(
                f"Invalid {field_name} format: {value}. Setting to 0"
            )
            return 0 if number_type is int else 0.0
