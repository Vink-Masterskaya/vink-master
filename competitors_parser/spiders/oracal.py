import json
import time
from typing import Dict, Any, Iterator
from scrapy import Request
from scrapy.http import Response
from .base import BaseCompetitorSpider


class OracalSpider(BaseCompetitorSpider):
    """Паук для парсинга сайта oracal-online.ru"""
    name = "oracal"
    allowed_domains = ["oracal-online.ru"]
    start_urls = ["https://api.oracal-online.ru/api/category/list/"]

    # API endpoints
    PRODUCT_LIST_URL = (
        'https://api.oracal-online.ru/api/product/category?page=1&slug={}'
    )
    PRODUCT_DETAIL_URL = (
        'https://api.oracal-online.ru/api/product-offer/'
        'list?slug={}&page=1&isAvailable=false'
    )

    # Задержки для API запросов
    CATEGORY_DELAY = 0.1
    PRODUCT_LIST_DELAY = 0.3
    PRODUCT_DETAIL_DELAY = 0.5

    custom_settings = {
        'CONCURRENT_REQUESTS': 8,
        'DOWNLOAD_DELAY': 1,
    }

    def parse(self, response: Response) -> Iterator[Request]:
        """Парсинг категорий"""
        try:
            # Загружаем JSON с API
            result = json.loads(response.body)

            self.logger.info(
                f"Получено {len(result.get('data', []))} основных категорий"
            )

            # Обрабатываем каждую категорию и подкатегорию
            for category in result.get('data', []):
                subcategories = category.get('subCategory', [])
                category_name = category.get('title', '')
                category_id = category.get('id', '')

                self.logger.info(
                    f"Обработка категории: {category_name} "
                    f"(ID: {category_id}, подкатегорий: {len(subcategories)})"
                )

                for subcategory in subcategories:
                    subcategory_id = subcategory.get('id', '')
                    subcategory_name = subcategory.get('title', '')
                    subcategory_slug = subcategory.get('slug', '')

                    # Полное название категории
                    full_cat = f"{category_name} - {subcategory_name}"

                    self.logger.info(
                        f"Подкатегория: {subcategory_name} (ID: {subcategory_id})"
                    )

                    # Добавляем задержку
                    time.sleep(self.CATEGORY_DELAY)

                    # Формируем URL для получения списка товаров
                    product_list_url = self.PRODUCT_LIST_URL.format(
                        subcategory_slug
                    )

                    yield Request(
                        url=product_list_url,
                        callback=self.parse_product_list,
                        cb_kwargs={'category': full_cat}
                    )

        except json.JSONDecodeError as e:
            self.logger.error(f"Ошибка при декодировании JSON: {str(e)}")
        except Exception as e:
            self.logger.error(
                f"Непредвиденная ошибка при обработке категорий: {str(e)}"
            )

    def parse_product_list(
            self,
            response: Response,
            category: str
            ) -> Iterator[Request]:
        """Парсинг списка товаров"""
        try:
            # Загружаем JSON с API
            result = json.loads(response.body)
            products = result.get('data', [])

            self.logger.info(
                f"Получено {len(products)} товаров в категории: {category}"
            )

            # Обрабатываем каждый товар
            for product in products:
                product_title = product.get('title', '')
                product_slug = product.get('slug', '')

                self.logger.info(
                    f"Обработка товара: {product_title} (slug: {product_slug})"
                )

                # Добавляем задержку
                time.sleep(self.PRODUCT_LIST_DELAY)

                # Формируем URL для получения деталей товара
                product_detail_url = self.PRODUCT_DETAIL_URL.format(
                    product_slug
                )

                yield Request(
                    url=product_detail_url,
                    callback=self.parse_product,
                    cb_kwargs={
                        'category': category,
                        'product_name': product_title
                    }
                )

        except json.JSONDecodeError as e:
            self.logger.error(
                f"Ошибка при декодировании JSON списка товаров: {str(e)}"
            )
        except Exception as e:
            self.logger.error(
                f"Непредвиденная ошибка при обработке товаров: {str(e)}"
            )

    def parse_product(
            self,
            response: Response,
            category: str,
            product_name: str
            ) -> Iterator[Dict[str, Any]]:
        """Парсинг данных о товаре"""
        try:
            # Загружаем JSON с API
            result = json.loads(response.body)

            # Получаем список вариантов товара
            offers = result.get('data', {}).get('offers', {}).get('data', [])

            self.logger.info(
                f"Получено {len(offers)} вариантов товара: {product_name}"
            )

            # Обрабатываем каждый вариант товара
            for offer in offers:
                # Добавляем задержку
                time.sleep(self.PRODUCT_DETAIL_DELAY)

                # Извлекаем данные о товаре
                offer_id = offer.get('id', '')
                offer_id_1s = offer.get('id_1s', '')
                offer_title = offer.get('title', '')

                # Получаем информацию о цене
                prices = offer.get('prices', [{}])
                price_value = prices[0].get('price', 0) if prices else 0
                price_unit = prices[0].get('unit', '') if prices else ''

                # Получаем информацию о наличии на складах
                stocks_data = offer.get('restsAvailable', [])

                # Преобразуем данные о складах в нужный формат
                stocks = self._format_stocks(stocks_data, price_value)

                # Формируем URL товара на сайте
                web_url = (
                    f"https://www.oracal-online.ru/product/{offer.get('slug', '')}"
                )

                self.logger.info(
                    f"Обработан вариант товара: {offer_title} (ID: {offer_id})"
                )

                # Создаем и возвращаем item
                yield {
                    'category': category,
                    'product_code': f"{offer_id_1s}/{offer_id}",
                    'name': offer_title,
                    'price': price_value,
                    'stocks': stocks,
                    'unit': price_unit,
                    'currency': 'RUB',
                    'weight': None,
                    'length': None,
                    'width': None,
                    'height': None,
                    'url': web_url
                }

        except json.JSONDecodeError as e:
            self.logger.error(
                f"Ошибка при декодировании JSON данных товара: {str(e)}"
            )
        except Exception as e:
            self.logger.error(
                f"Непредвиденная ошибка при обработке данных товара: {str(e)}"
            )

    def _format_stocks(self, stocks_data: list, price: float) -> list:
        """
        Форматирует данные о складах в требуемом формате

        Args:
            stocks_data: Данные о складах из API
            price: Цена товара

        Returns:
            list: Отформатированные данные о складах
        """
        # Всегда имеем две записи: "Москва" и "На других складах"
        moscow_quantity = 0
        other_quantity = 0

        # Обрабатываем данные о складах, если они есть
        if stocks_data:
            for stock in stocks_data:
                store_name = stock.get('store', {}).get('name', '')
                quantity = stock.get('rest', 0)

                if store_name == 'Москва':
                    moscow_quantity = quantity
                else:
                    other_quantity += quantity

        # Формируем результат
        formatted_stocks = [
            {
                "stock": "Москва",
                "quantity": moscow_quantity,
                "price": price
            },
            {
                "stock": "На других складах",
                "quantity": other_quantity,
                "price": price
            }
        ]

        return formatted_stocks
