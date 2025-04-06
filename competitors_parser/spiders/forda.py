import json
from typing import Any, Dict, Iterator, List, Optional

import requests
from scrapy import Request
from scrapy.http import Response

from .base import BaseCompetitorSpider


class FordaSpider(BaseCompetitorSpider):
    """Паук для парсинга сайта forda.ru."""
    name = 'forda'
    allowed_domains = ['forda.ru', 'www.forda.ru']
    start_urls = ['https://www.forda.ru/katalog/']
    local_warehouses = ['Подольск', 'Подольск-транзит', 'Москва']

    # Исключаем категории из парсинга
    excluded_categories = ['Новинки', 'Распродажа']

    def parse(self, response: Response) -> Iterator[Request]:
        """Парсинг главной страницы каталога."""
        all_categories = response.css('a.card-header')

        for category in all_categories:
            category_name = category.css('::text').get()
            category_url = category.css('::attr(href)').get()

            # Пропускаем исключенные категории
            if category_name in self.excluded_categories:
                continue

            if category_url:
                self.logger.info(
                    f'Категория: {category_name} - {category_url}'
                    )

                yield Request(
                    url=response.urljoin(category_url),
                    callback=self.parse_category,
                    cb_kwargs={
                        'category': category_name,
                        'processed_urls': set()
                        }
                )

    def parse_category(
            self,
            response: Response,
            category: str,
            processed_urls: set
            ) -> Iterator[Request]:
        """Парсинг страницы категории или товара."""
        self.logger.info(f'Обработка URL: {response.url}')

        # Проверяем, является ли страница страницей товара
        api_id = self._get_api_id(response)
        offer_id = self._get_offer_id(response)

        # Если нашли идентификаторы API и оффера, это страница товара
        if api_id and offer_id:
            self.logger.info(
                f'Обрабатываем товар: API ID={api_id}, Offer ID={offer_id}'
                )
            yield from self._process_product(
                response,
                category,
                api_id,
                offer_id
                )

        # Ищем ссылки на другие товары
        products_table = response.xpath('//*[@class="catalog-section card"]')
        products = products_table.css('a::attr(href)').getall()

        for product_url in products:
            full_url = response.urljoin(product_url)

            # Избегаем повторной обработки URL
            if full_url not in processed_urls:
                processed_urls.add(full_url)
                self.logger.info(f'Найдена ссылка на товар: {product_url}')

                yield Request(
                    url=full_url,
                    callback=self.parse_category,
                    cb_kwargs={
                        'category': category,
                        'processed_urls': processed_urls
                        }
                )

    def _process_product(
            self,
            response: Response,
            category: str,
            api_id: str,
            offer_id: str
            ) -> Iterator[Dict[str, Any]]:
        """Обработка страницы товара."""
        try:
            # Получаем название продукта
            product_name = response.css('h1::text').get()
            if not product_name:
                return

            product_name = self.clean_text(product_name)

            # Получаем информацию о складах через API
            stocks_data = self._get_stocks_data(api_id)

            if not stocks_data:
                self.logger.warning(
                    f'Нет данных о складах для товара {api_id}'
                    )
                return

            for product_variant in stocks_data:
                variant_name = product_variant.get('name', '')
                if isinstance(variant_name, tuple):
                    variant_name = variant_name[0] if variant_name else ''

                price = product_variant.get('price', 0.0)
                stocks = product_variant.get('stocks', [])

                # Формируем полное название товара
                name = ' ' + variant_name if variant_name and variant_name != '' else ''
                full_name = f'{product_name}{name}'

                # Проверка наличия складов
                if not stocks:
                    stocks = [{
                        'stock': 'Основной',
                        'quantity': 0,
                        'price': price
                    }]

                item = {
                    'category': category,
                    'product_code': f'{offer_id} / {api_id}',
                    'name': full_name,
                    'stocks': stocks,
                    'unit': 'шт',
                    'currency': 'RUB',
                    'url': response.url
                }

                self.logger.info(
                    f'Обработан товар: {full_name} с {len(stocks)} складами'
                    )
                yield item

        except Exception as e:
            self.logger.error(
                f'Ошибка обработки товара {response.url}: {str(e)}'
                )

    def _get_api_id(self, response: Response) -> Optional[str]:
        """Извлечение API ID из скрипта на странице."""
        script_text = response.xpath(
            '//script[contains(., "productId")]/text()'
            ).get()
        if not script_text:
            return None

        try:
            start_idx = script_text.find('(')
            end_idx = script_text.find(')')
            if start_idx != -1 and end_idx != -1:
                return script_text[start_idx + 1:end_idx].strip()
        except Exception as e:
            self.logger.error(f'Ошибка извлечения API ID: {str(e)}')

        return None

    def _get_offer_id(self, response: Response) -> Optional[str]:
        """Извлечение Offer ID из скрипта на странице."""
        script_text = response.xpath(
            '//script[contains(., "offer_id")]/text()'
            ).get()
        if not script_text:
            return None

        try:
            start_idx = script_text.find('offer_id:') + 11
            if start_idx != -1:
                raw_offer_id = script_text[start_idx:start_idx + 50]
                offer_id = self.clean_text(raw_offer_id.replace("'", ''))
                return offer_id
        except Exception as e:
            self.logger.error(f'Ошибка извлечения Offer ID: {str(e)}')

        return None

    def _get_stocks_data(self, api_id: str) -> List[Dict[str, Any]]:
        """Получение данных о наличии товара через API."""
        url = f'https://www.forda.ru/get_offers?id={api_id}'

        try:
            # Делаем запрос к API
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Проверяем, что данные не пустые
            if not data:
                self.logger.warning(f'Пустой ответ API для товара {api_id}')
                return []

            result = []
            # Обрабатываем каждый вариант продукта
            for product in data:
                product_name = product.get('name', '')
                product_price = product.get(
                    'prices', [{}])[0].get('price', 0.0)

                # Собираем информацию о складах
                stocks = []
                for warehouse in product.get('restsWarehouses', []):
                    store_info = warehouse.get('store', {})
                    store_name = store_info.get('name', 'Основной')
                    rest_qty = warehouse.get('rest', 0)

                    # Добавляем информацию о местном складе
                    stocks.append({
                        'stock': store_name,
                        'quantity': rest_qty,
                        'price': product_price
                    })

                for rest in product.get('rests', []):
                    store_info = rest.get('store', {})
                    store_name = store_info.get('name', 'На других')
                    rest_qty = rest.get('rest', 0)

                    # Добавляем информацию о других складах
                    if store_name not in self.local_warehouses:
                        stocks.append({
                            'stock': store_name,
                            'quantity': rest_qty,
                            'price': product_price
                        })

                # Логируем информацию о найденных складах
                self.logger.info(
                    f'Найдено {len(stocks)} складов для товара {product_name}'
                    )

                # Добавляем данные о продукте с информацией о складах
                result.append({
                    'name': product_name,
                    'price': product_price,
                    'stocks': stocks
                })

            return result

        except requests.RequestException as e:
            self.logger.error(f'Ошибка запроса API для {api_id}: {str(e)}')
        except (ValueError, json.JSONDecodeError) as e:
            self.logger.error(f'Ошибка парсинга JSON для {api_id}: {str(e)}')
        except Exception as e:
            self.logger.error(
                f'Непредвиденная ошибка при получении данных о складах для {api_id}: {str(e)}'
                )

        return []
