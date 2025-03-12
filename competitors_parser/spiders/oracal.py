import json
import time
from typing import Any, Dict, Iterator, List

from scrapy import Request
from scrapy.http import Response

from .base import BaseCompetitorSpider


class OracalSpider(BaseCompetitorSpider):
    """Паук для парсинга сайта oracal-online.ru."""
    name = 'oracal'
    allowed_domains = ['oracal-online.ru']
    start_urls = ['https://api.oracal-online.ru/api/category/list/']

    # API URL шаблоны
    BASE_PROD_LIST_URL = 'https://api.oracal-online.ru/api/product/category?page=1&slug='
    BASE_PROD_URL_BEGIN = 'https://api.oracal-online.ru/api/product-offer/list?slug='
    BASE_PROD_URL_END = '&page=1&isAvailable=false'
    BASE_SUBCAT_URL = 'https://api.oracal-online.ru/api/category?slug='

    # Настройки для API запросов
    custom_settings = {
        'DOWNLOAD_DELAY': 0.5,
        'CONCURRENT_REQUESTS': 8,
        'RETRY_ENABLED': True,
        'RETRY_TIMES': 3,
    }

    def parse(self, response: Response) -> Iterator[Request]:
        """Парсинг категорий с API."""
        self.logger.info('Начинаем парсинг категорий Oracal')

        try:
            result = json.loads(response.body)

            for category in result.get('data', []):
                subcats = category.get('subCategory', [])
                category_title = category.get('title', '')

                self.logger.info(f'Обрабатываем категорию: {category_title}')

                for sub in subcats:
                    sub_slug = sub.get('slug', '')
                    sub_title = sub.get('title', '')

                    if not sub_slug:
                        continue

                    url = f'{self.BASE_SUBCAT_URL}{sub_slug}'

                    yield Request(
                        url=url,
                        callback=self.parse_category,
                        cb_kwargs={
                            'cat': f'{category_title} - {sub_title}',
                            'sub': sub_slug
                        },
                        dont_filter=True
                    )
                    time.sleep(0.1)

        except json.JSONDecodeError as e:
            self.logger.error(f'Ошибка декодирования JSON: {str(e)}')
        except Exception as e:
            self.logger.error(f'Ошибка при парсинге категорий: {str(e)}')

    def parse_category(
            self,
            response: Response,
            cat: str,
            sub: str
            ) -> Iterator[Request]:
        """Парсинг подкатегорий и поиск товаров."""
        try:
            result = json.loads(response.body)
            data = result.get('data', {}).get('subCategories', [])

            if len(data) > 0:
                self.logger.info(f'Найдено {len(data)} подкатегорий в {cat}')

                for subcategory in data:
                    sub_slug = subcategory.get('slug', '')

                    if not sub_slug:
                        continue

                    url = f'{self.BASE_SUBCAT_URL}{sub_slug}'

                    yield Request(
                        url=url,
                        callback=self.parse_category,
                        cb_kwargs={
                            'cat': cat,
                            'sub': sub_slug
                        },
                        dont_filter=True
                    )
                    time.sleep(0.3)
            else:
                url = f'{self.BASE_PROD_LIST_URL}{sub}'

                yield Request(
                    url=url,
                    callback=self.parse_product_list,
                    cb_kwargs={'cat': cat},
                    dont_filter=True
                )
                time.sleep(0.3)

        except json.JSONDecodeError as e:
            self.logger.error(f'Ошибка декодирования JSON: {str(e)}')
        except Exception as e:
            self.logger.error(f'Ошибка при парсинге категории {cat}: {str(e)}')

    def parse_product_list(
            self,
            response: Response,
            cat: str
            ) -> Iterator[Request]:
        """Парсинг списка товаров в категории."""
        try:
            result = json.loads(response.body)
            products = result.get('data', [])

            self.logger.info(f'Найдено {len(products)} товаров в {cat}')

            for product in products:
                product_slug = product.get('slug', '')
                product_title = product.get('title', '')

                if not product_slug:
                    continue

                url = f'{self.BASE_PROD_URL_BEGIN}{product_slug}{self.BASE_PROD_URL_END}'

                yield Request(
                    url=url,
                    callback=self.parse_product,
                    cb_kwargs={'cat': f'{cat} --- {product_title}'},
                    dont_filter=True
                )
                time.sleep(0.3)

        except json.JSONDecodeError as e:
            self.logger.error(f'Ошибка декодирования JSON: {str(e)}')
        except Exception as e:
            self.logger.error(f'Ошибка при обработке списка товаров: {str(e)}')

    def parse_product(
            self,
            response: Response,
            cat: str
            ) -> Iterator[Dict[str, Any]]:
        """Парсинг данных о товаре."""
        try:
            result = json.loads(response.body)
            data = result.get('data', {}).get('offers', {}).get('data', [])

            for product in data:
                product_id = product.get('id', '')
                product_title = product.get('title', '')
                product_id_1s = product.get('id_1s', '')

                # Формирование корректного URL для товара
                product_url = f'https://www.oracal-online.ru/offer/{product_id}'

                # Получаем основную единицу измерения товара
                main_unit = product.get('unit', 'шт')

                # Получаем цену для основной единицы измерения
                main_price = self._get_price_for_unit(product, main_unit)

                # Получаем информацию о складах
                stocks = self._get_normalized_stocks(product)

                # Получаем характеристики
                properties = product.get('properties', [])
                color = weight = width = length = None

                for property in properties:
                    prop_name = property.get('name', '').lower()
                    prop_value = property.get('value', '')

                    if 'цвет' in prop_name:
                        color = prop_value
                    elif 'вес' in prop_name:
                        weight = prop_value
                    elif 'ширина' in prop_name:
                        width = prop_value
                    elif 'длина' in prop_name:
                        length = prop_value

                yield {
                    'category': cat,
                    'product_code': f'{product_id_1s}/{product_id}',
                    'name': product_title,
                    'price': main_price,
                    'stocks': stocks,
                    'unit': main_unit,
                    'currency': 'RUB',
                    'weight': weight,
                    'width': width,
                    'length': length,
                    'height': None,
                    'url': product_url,
                }
                time.sleep(0.5)

        except json.JSONDecodeError as e:
            self.logger.error(f'Ошибка декодирования JSON: {str(e)}')
        except Exception as e:
            self.logger.error(f'Ошибка при обработке товара: {str(e)}')

    def _get_price_for_unit(self, product: Dict[str, Any], unit: str) -> float:
        """Получение цены товара для конкретной единицы измерения."""
        prices = product.get('prices', [])

        # Ищем цену для заданной единицы измерения
        for price_item in prices:
            if price_item.get('unit') == unit:
                try:
                    return float(price_item.get('price', 0.0))
                except (ValueError, TypeError):
                    self.logger.warning(f'Ошибка преобразования цены для {unit}')
                    return 0.0

        # Если не нашли подходящую цену, возвращаем первую доступную
        if prices:
            try:
                return float(prices[0].get('price', 0.0))
            except (ValueError, TypeError):
                self.logger.warning('Ошибка преобразования цены')
                return 0.0

        return 0.0

    def _get_normalized_stocks(
            self,
            product: Dict[str, Any]
            ) -> List[Dict[str, Any]]:
        """Нормализация данных о складах с учетом разных цен по единицам измерения."""
        result = []

        # Словарь для хранения информации о наличии по единицам измерения
        units_quantity = {}

        # Собираем информацию из restsAllStore (все склады)
        all_stores = product.get('restsAllStore', [])
        for store in all_stores:
            unit_value = store.get('value', '')  # "rul", "pogm" и т.д.
            unit_title = store.get('title', '')  # Человекочитаемое название, например "рул", "пог. м"
            amount = store.get('amount', 0)

            # Добавляем в словарь для подсчета общего количества по единицам измерения
            if unit_value not in units_quantity:
                units_quantity[unit_value] = {
                    'title': unit_title,
                    'amount': amount
                }
            else:
                units_quantity[unit_value]['amount'] += amount

        # Формируем записи о наличии на складах
        for unit_value, data in units_quantity.items():
            # Получаем цену для данной единицы измерения
            unit_price = self._get_price_for_unit(product, data['title'])

            result.append({
                'stock': f"Все склады ({data['title']})",
                'quantity': data['amount'],
                'price': unit_price
            })

        # Если restsAvailable также содержит данные, добавляем отдельные записи для текущего города
        available = product.get('restsAvailable', [])
        for store in available:
            unit_value = store.get('value', '')
            unit_title = store.get('title', '')
            amount = store.get('amount', 0)

            # Получаем цену для данной единицы измерения
            unit_price = self._get_price_for_unit(product, unit_title)

            # Добавляем информацию о наличии в текущем городе
            if amount > 0:
                result.append({
                    'stock': f"Текущий город ({unit_title})",
                    'quantity': amount,
                    'price': unit_price
                })

        # Если не удалось найти данные о наличии, добавляем пустую запись
        if not result:
            result.append({
                'stock': 'Нет в наличии',
                'quantity': 0,
                'price': self._get_price_for_unit(product, product.get('unit', 'шт'))
            })

        return result
