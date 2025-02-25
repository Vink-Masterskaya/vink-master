from typing import Dict, Any, Iterator
from scrapy import Request
from scrapy.http import Response
from .base import BaseCompetitorSpider


class RemexSpider(BaseCompetitorSpider):
    """Паук для парсинга сайта remex.ru"""
    name = "remex"
    allowed_domains = ["remex.ru"]
    start_urls = ["https://www.remex.ru/price"]

    category_mapping = {
        'мобильные': 'мобильные стенды',
        'стенды': 'Инструменты, крепёж'
    }

    def parse(self, response: Response) -> Iterator[Request]:
        """Парсинг главной страницы каталога"""
        all_categories = response.css('a[href^="/price/"]')

        for category in all_categories:
            category_name = category.css('span::text').get('')
            category_url = category.css('::attr(href)').get()

            if not category_url:
                continue

            # Нормализация названия категории
            category_name = self.category_mapping.get(
                category_name,
                category_name
            )

            if category_name:
                category_name = category_name.capitalize()

            self.logger.info(
                'Processing category: %s (%s)',
                category_name,
                category_url
            )

            yield Request(
                url=response.urljoin(category_url),
                callback=self.parse_category,
                cb_kwargs={'category': category_name}
            )

    def parse_category(
            self,
            response: Response,
            category: str
            ) -> Iterator[Request]:
        """Парсинг страницы категории"""
        products_table = response.xpath(
            '//*[@class="price-table price-table-images"]'
        )

        for product_link in products_table.css('a::attr(href)').getall():
            if not product_link:
                continue

            self.logger.info('Processing product: %s', product_link)

            yield Request(
                url=response.urljoin(product_link),
                callback=self.parse_product,
                cb_kwargs={'category': category}
            )

    def parse_product(
            self,
            response: Response,
            category: str
            ) -> Iterator[Dict[str, Any]]:
        """Парсинг карточки товара"""
        product_table = response.xpath('//*[@class="price-table pprtbl"]')
        rows = product_table.css('tr')

        for row in rows:
            cells = row.css('td::text').getall()
            if len(cells) != 3:
                continue

            name, unit, price_str = [self.clean_text(cell) for cell in cells]

            # Валидация обязательных полей
            if not name or not price_str:
                continue

            try:
                price = self.extract_price(price_str)
            except ValueError:
                self.logger.warning(
                    'Invalid price format for product %s: %s',
                    name,
                    price_str
                )
                continue

            # Создаем структуру данных согласно ТЗ
            yield {
                'category': category,
                'product_code': name,
                'name': name,
                'price': price,
                'stocks': [{
                    'stock': 'Москва',
                    'quantity': 0,
                    'price': price
                }],
                'unit': unit,
                'currency': 'RUB',
                'weight': None,
                'length': None,
                'width': None,
                'height': None,
                'url': response.url,
            }
