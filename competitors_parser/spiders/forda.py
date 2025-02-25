from typing import Dict, Any, List, Set, Optional, Iterator
import json
import aiohttp
from scrapy import Request
from scrapy.http import Response
from .base import BaseCompetitorSpider


class FordaSpider(BaseCompetitorSpider):
    """Паук для парсинга сайта forda.ru"""
    name = "forda"
    allowed_domains = ["forda.ru", "www.forda.ru"]
    start_urls = ["https://www.forda.ru/katalog/"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.processed_urls = set()  # Для отслеживания уже обработанных URL

    def parse(self, response: Response) -> Iterator[Request]:
        """Парсинг главной страницы каталога"""
        all_categories = response.css('a.card-header')
        links = all_categories.css('::attr(href)').getall()
        category_names = all_categories.css('::text').getall()

        for category_name, category_link in zip(category_names, links):
            category_name = self.clean_text(category_name)

            # Пропускаем ненужные категории
            if category_name not in ['Новинки', 'Распродажа']:
                self.logger.info(
                    f'Processing category: {category_name} - {category_link}')

                yield Request(
                    url=response.urljoin(category_link),
                    callback=self.parse_category,
                    cb_kwargs={
                        'category': category_name,
                        'processed_urls': set()
                        # Отдельный набор для каждой категории
                    }
                )

    def parse_category(
            self,
            response: Response,
            category: str,
            processed_urls: Set[str]
            ) -> Iterator[Request]:
        """Парсинг страницы категории или товара"""
        # Проверяем, является ли страница товаром
        product_title = response.css('h1::text').get()

        if product_title:
            # Это страница товара
            try:
                yield from self.parse_product(response, category)
            except Exception as e:
                self.logger.error(
                    f"Error parsing product {response.url}: {str(e)}")

        # В любом случае продолжаем искать ссылки на другие товары
        products_table = response.xpath('//*[@class="catalog-section card"]')

        for product_url in products_table.css('a::attr(href)').getall():
            product_url = response.urljoin(product_url)

            # Проверяем, не обрабатывали ли мы уже этот URL
            if product_url not in processed_urls and product_url not in self.processed_urls:
                processed_urls.add(product_url)
                self.processed_urls.add(product_url)

                self.logger.info(f'Found product: {product_url}')

                yield Request(
                    url=product_url,
                    callback=self.parse_category,
                    cb_kwargs={
                        'category': category,
                        'processed_urls': processed_urls
                    }
                )

    def parse_product(
            self,
            response: Response,
            category: str
            ) -> Iterator[Dict[str, Any]]:
        """Парсинг данных товара"""
        # Извлекаем название продукта
        product_name = self.clean_text(response.css('h1::text').get())
        if not product_name:
            return

        # Извлекаем API ID и Offer ID из скриптов
        api_id = self._get_api_id(
            response.xpath('//script[contains(., "productId")]/text()').get())
        offer_id = self._get_offer_id(
            response.xpath('//script[contains(., "offer_id")]/text()').get())

        if not api_id or not offer_id:
            self.logger.warning(
                f"Could not extract API ID or Offer ID for {response.url}"
                )
            return

        # Получаем информацию о складах
        stocks_data = yield from self._get_stocks(api_id)

        if not stocks_data:
            self.logger.warning(f"No stock data for product {response.url}")
            # Создаем элемент без информации о складах
            yield {
                'category': category,
                'product_code': f'{offer_id} / {api_id}',
                'name': product_name,
                'price': self._extract_price_from_response(response),
                'stocks': [],
                'unit': 'шт',
                'currency': 'RUB',
                'weight': None,
                'length': None,
                'width': None,
                'height': None,
                'url': response.url
            }
            return

        # Создаем элемент с информацией о складах
        for stock_item in stocks_data:
            stock_name = stock_item.get("name", "")
            stock_price = stock_item.get("price", 0.0)

            stocks = []
            for stock_info in stock_item.get("stocks", []):
                stocks.append({
                    'stock': stock_info.get('city', 'Неизвестный'),
                    'quantity': stock_info.get('quantity', 0),
                    'price': stock_price
                })

            # Если нет информации о складах, добавляем пустой список
            if not stocks:
                stocks = [{
                    'stock': 'Основной',
                    'quantity': 0,
                    'price': stock_price
                }]

            full_name = f"{product_name} {stock_name}".strip()

            yield {
                'category': category,
                'product_code': f'{offer_id} / {api_id}',
                'name': full_name,
                'price': stock_price,
                'stocks': stocks,
                'unit': 'шт',
                'currency': 'RUB',
                'weight': None,
                'length': None,
                'width': None,
                'height': None,
                'url': response.url
            }

    async def _get_stocks(self, api_id: str) -> List[Dict[str, Any]]:
        """Получение информации о наличии товара на складах через API"""
        if not api_id:
            self.logger.warning("Empty API ID provided")
            return []

        try:
            api_url = f"https://www.forda.ru/api/product/{api_id}/stocks"

            async with aiohttp.ClientSession() as session:
                async with session.get(api_url) as response:
                    if response.status != 200:
                        self.logger.error(
                            f"API error: Status {response.status}"
                            )
                        return []

                    data = await response.json()

                    # Проверяем структуру ответа
                    if not isinstance(data, list):
                        self.logger.warning(
                            f"Unexpected API response format: {type(data)}"
                            )
                        return []

                    return data

        except aiohttp.ClientError as e:
            self.logger.error(f"HTTP request error: {str(e)}")
            return []
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error: {str(e)}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error getting stock data: {str(e)}")
            return []

    def _extract_price_from_response(self, response: Response) -> float:
        """Извлечение цены из страницы товара"""
        price_text = response.xpath('//*[@class="h1 text-primary"]/text()').get()
        if price_text:
            return self.extract_price(price_text)
        return 0.0

    def _get_api_id(self, script_text: Optional[str]) -> Optional[str]:
        """Извлечение API ID из скрипта на странице"""
        if not script_text:
            return None

        try:
            # Пример: productId: '12345'
            start_index = script_text.find('(')
            end_index = script_text.find(')')

            if start_index != -1 and end_index != -1:
                return script_text[start_index + 1:end_index].strip()
        except Exception as e:
            self.logger.error(f"Error extracting API ID: {str(e)}")

        return None

    def _get_offer_id(self, script_text: Optional[str]) -> Optional[str]:
        """Извлечение Offer ID из скрипта на странице"""
        if not script_text:
            return None

        try:
            # Пример: offer_id: '67890'
            start_text = 'offer_id:'
            start_index = script_text.find(start_text)

            if start_index != -1:
                # Извлекаем подстроку после 'offer_id:'
                substring = script_text[start_index + len(start_text):start_index + 50]
                # Очищаем от лишних символов
                cleaned = self.clean_text(substring.replace("'", ''))
                return cleaned
        except Exception as e:
            self.logger.error(f"Error extracting Offer ID: {str(e)}")

        return None
