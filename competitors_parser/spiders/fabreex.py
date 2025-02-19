import scrapy
from typing import Dict, Any, Optional
from scrapy.http import Response
from .base import BaseCompetitorSpider


class FabreexSpider(BaseCompetitorSpider):
    name = 'fabreex'
    allowed_domains = ['fabreex.ru']
    start_urls = ['https://fabreex.ru/catalog/']

    def parse(self, response: Response):
        """Парсинг главной страницы каталога"""
        all_categories = response.css('.uk-button')
        links = all_categories.css('a::attr(href)').getall()
        categories = all_categories.css('a::text').getall()

        for category_name, category_link in zip(categories, links):
            category = self.clean_text(category_name)
            self.logger.info(f'Category link: {category} - {category_link}')

            yield scrapy.Request(
                url=response.urljoin(category_link),
                callback=self.parse_category,
                cb_kwargs={'category': category}
            )

    def parse_category(self, response: Response, category: str):
        """Парсинг страницы категории"""
        products_table = response.xpath(
            '//*[@class="sz-cards-bottom sz-cards-bottom-new"]'
        )
        self.logger.info(f'Processing category: {category}')

        products = products_table.css('a::attr(href)').getall()
        for product_url in products:
            self.logger.info(f'Product link: {product_url}')
            yield scrapy.Request(
                url=response.urljoin(product_url),
                callback=self.parse_product,
                cb_kwargs={'category': category}
            )

    def parse_product(
        self,
        response: Response,
        category: str
    ) -> Optional[Dict[str, Any]]:
        """Парсинг страницы товара"""
        try:
            name = response.css('h1::text').get()
            if not name:
                return None
            name = self.clean_text(name)

            # Получаем базовую цену
            price_text = response.css('.sz-full-price-prod::text').get()
            base_price = self.extract_price(price_text) if price_text else 0.0

            # Получаем доступные цвета
            color_elements = response.css('.desc-color-element')
            if not color_elements:
                # Если нет выбора цветов, обрабатываем как один товар
                return self._create_item(
                    name=name,
                    price=base_price,
                    category=category,
                    response=response
                )

            items = []
            # Обрабатываем каждый цвет как отдельный товар
            for color_element in color_elements:
                # Получаем цену для конкретного цвета
                color_price_text = color_element.css(
                    '.color-price::text'
                    ).get()
                color_price = (
                    self.extract_price(
                        color_price_text) if color_price_text else base_price)

                # Получаем название цвета
                color_name = (color_element.css(
                    '::attr(title)').get() or 'Стандартный')
                color_name = self.clean_text(color_name)

                # Формируем название с учетом цвета
                full_name = f"{name} ({color_name})"

                item = self._create_item(
                    name=full_name,
                    price=color_price,
                    category=category,
                    response=response
                )
                items.append(item)

            return items[0] if items else None

        except Exception as e:
            self.logger.error(
                f"Error parsing product {response.url}: {str(e)}"
            )
            return None

    def _create_item(
        self,
        name: str,
        price: float,
        category: str,
        response: Response
    ) -> Dict[str, Any]:
        """Создание item'а с общими параметрами"""
        units = response.xpath(
            '//*[@class="uk-position-relative uk-position-z-index"]'
            '/text()'
        ).getall()[:2]
        unit = str(units).strip() if units else "шт."

        quantity_text = response.css('input[type="number"]::attr(max)').get()
        quantity = self.extract_stock(quantity_text) if quantity_text else 0

        stocks = [{
            'stock': 'Санкт-Петербург',
            'quantity': quantity,
            'price': price
        }]

        return {
            'category': category,
            'product_code': self.clean_text(name),
            'name': name,
            'price': price,
            'stocks': stocks,
            'unit': unit,
            'currency': 'RUB',
            'url': response.url
        }
