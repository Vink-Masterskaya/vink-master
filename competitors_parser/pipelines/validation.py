import logging
from typing import Any, Dict, List, Optional, Union

from scrapy.exceptions import DropItem


class ValidationPipeline:
    """Валидация данных перед сохранением и приведение к единому формату."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        self.required_fields = ['product_code', 'name']

    def process_item(self, item: Dict[str, Any], spider) -> Dict[str, Any]:
        """Валидация и стандартизация данных для всех пауков."""
        # Проверка обязательных полей
        for field in self.required_fields:
            if not item.get(field):
                msg = f'Отсутствует обязательное поле: {field}'
                self.logger.warning(msg)
                raise DropItem(msg)

        price = item.get('price')
        stocks = item.get('stocks', [])

        has_valid_price = price is not None
        has_stocks_with_price = False

        # Проверяем, есть ли цены в stocks
        if stocks:
            for stock in stocks:
                if stock.get('price') is not None:
                    has_stocks_with_price = True
                    break

        if not has_valid_price and not has_stocks_with_price:
            msg = 'Отсутствует информация о цене (ни в поле price, ни в stocks)'
            self.logger.warning(msg)
            raise DropItem(msg)

        normalized_item = {
            'category': self._get_str_value(item, 'category', ''),
            'product_code': self._get_str_value(item, 'product_code', ''),
            'name': self._get_str_value(item, 'name', ''),
            'stocks': self._normalize_stocks(item),
            'unit': self._normalize_unit(item),
            'currency': self._get_str_value(item, 'currency', 'RUB'),
            'url': self._get_str_value(item, 'url', ''),
            'weight': self._get_str_value(item, 'weight', None),
            'length': self._get_str_value(item, 'length', None),
            'width': self._get_str_value(item, 'width', None),
            'height': self._get_str_value(item, 'height', None),
        }

        return normalized_item

    def _get_str_value(
            self,
            item: Dict[str, Any],
            key: str,
            default: Optional[str] = ''
            ) -> Optional[str]:
        """Получение строкового значения."""
        value = item.get(key, default)
        if value is None:
            return None
        return str(value).strip()

    def _get_float_value(
            self,
            item: Dict[str, Any],
            key: str,
            default: float = 0.0
            ) -> float:
        """Получение числового значения как float."""
        value = item.get(key, default)
        if value is None:
            return default
        try:
            # Преобразуем строку в число, заменяя запятую на точку
            if isinstance(value, str):
                value = value.replace(',', '.')
            return float(value)
        except (ValueError, TypeError):
            self.logger.warning(
                f'Неверное значение для {key}: {value}, используем значение по умолчанию {default}'
                )
            return default

    def _normalize_stocks(self, item: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Нормализация данных о наличии товара на складах."""
        if 'stocks' in item and isinstance(item['stocks'], list):
            return [
                self._normalize_stock_item(stock) for stock in item['stocks']
                ]

        # Если есть поля stock и city - преобразуем в формат stocks
        if 'stock' in item or 'city' in item:
            stock_name = item.get('city', 'Основной')
            quantity = item.get('stock', 0)

            # Если quantity это строка типа "По запросу", преобразуем в 0
            if isinstance(quantity, str) and not quantity.isdigit():
                quantity = 0

            try:
                quantity = int(quantity)
            except (ValueError, TypeError):
                quantity = 0

            price = self._get_float_value(item, 'price', 0.0)

            return [{
                'stock': stock_name,
                'quantity': quantity,
                'price': price
            }]

        # Если нет информации о складе, но есть цена, создаем склад по умолчанию
        if 'price' in item and item['price'] is not None:
            return [{
                'stock': 'Основной',
                'quantity': 0,
                'price': self._get_float_value(item, 'price', 0.0)
            }]

        return []

    def _normalize_stock_item(self, stock: Dict[str, Any]) -> Dict[str, Any]:
        """Нормализация отдельной записи о складе."""
        return {
            'stock': self._get_str_value(stock, 'stock', 'Основной'),
            'quantity': self._get_int_value(stock, 'quantity', 0),
            'price': self._get_float_value(stock, 'price', 0.0)
        }

    def _get_int_value(
            self,
            item: Dict[str, Any],
            key: str,
            default: int = 0
            ) -> int:
        """Получение числового значения как int."""
        try:
            value = item.get(key, default)
            if value is None:
                return default
            return int(float(value))
        except (ValueError, TypeError):
            self.logger.warning(
                f'Неверное значение для {key}: {value}, используем значение по умолчанию {default}'
                )
            return default

    def _normalize_unit(self, item: Dict[str, Any]) -> Union[str, List[str]]:
        """Нормализация единицы измерения."""
        unit = item.get('unit')

        # Если единицы измерения нет, возвращаем значение по умолчанию
        if not unit:
            return 'шт'

        # Если единица измерения уже в виде списка, возвращаем как есть
        if isinstance(unit, list):
            return unit

        # Иначе возвращаем как строку
        return str(unit).strip()
