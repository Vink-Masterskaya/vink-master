from typing import Dict, Any, Optional, Iterator
from scrapy import Spider, Request
from scrapy.http import Response
import re
from .base import BaseCompetitorSpider


class FabreexSpider(BaseCompetitorSpider):
    name = 'fabreex'
    allowed_domains = ['fabreex.ru']
    start_urls = ['https://fabreex.ru/catalog/']

    def parse(self, response: Response) -> Iterator[Request]:
        """Парсинг главной страницы каталога"""
        all_categories = response.css('.uk-button')
        links = all_categories.css('a::attr(href)').getall()
        categories = all_categories.css('a::text').getall()

        for category_name, category_link in zip(categories, links):
            category = self.clean_text(category_name)
            self.logger.info(
                f'Category link: {category} - {category_link}'
            )

            yield Request(
                url=response.urljoin(category_link),
                callback=self.parse_category,
                cb_kwargs={'category': category}
            )

    def parse_category(
        self, response: Response, category: str
    ) -> Iterator[Request]:
        """Парсинг страницы категории"""
        products_table = response.xpath(
            '//*[@class="sz-cards-bottom sz-cards-bottom-new"]'
        )
        self.logger.info(f'Processing category: {category}')

        products = products_table.css('a::attr(href)').getall()
        for product_url in products:
            self.logger.info(f'Product link: {product_url}')
            yield Request(
                url=response.urljoin(product_url),
                callback=self.parse_product,
                cb_kwargs={'category': category}
            )

        next_page = response.css(
            '.uk-pagination .uk-active + li a::attr(href)'
        ).get()
        if next_page:
            self.logger.info(f'Next page link: {next_page}')
            yield Request(
                url=response.urljoin(next_page),
                callback=self.parse_category,
                cb_kwargs={'category': category}
            )

    def parse_product(
        self, response: Response, category: str
    ) -> Iterator[Dict[str, Any]]:
        """Парсинг страницы товара"""
        try:
            name = response.css('h1::text').get()
            if not name:
                return
            name = self.clean_text(name)

            price_text = response.css('.sz-full-price-prod::text').get()
            price = self.extract_price(price_text) if price_text else 0.0

            yield self._create_item(
                name=name,
                price=price,
                category=category,
                response=response
            )

            color_links = response.css(
                '.desc-color-element::attr(href)'
            ).getall()

            for color_link in color_links:
                if color_link:
                    yield Request(
                        url=response.urljoin(color_link),
                        callback=self.parse_product,
                        cb_kwargs={'category': category}
                    )

        except Exception as e:
            self.logger.error(
                f"Error parsing product {response.url}: {str(e)}"
            )

    def _create_item(
        self, name: str, price: float, category: str, response: Response
    ) -> Dict[str, Any]:
        """Создание item'а с общими параметрами"""
        # Парсим юнит
        units = response.xpath(
            '//*[@class="uk-position-relative uk-position-z-index"]'
            '/text()'
        ).getall()[:2]

        if units:
            if all(unit.strip() == 'За шт.' for unit in units):
                unit = 'За шт.'
            else:
                unit = [unit.strip() for unit in units]
        else:
            unit = 'За шт.'

        # Парсим количество
        quantity_text = response.css('input[type="number"]::attr(max)').get()
        quantity = self.extract_stock(quantity_text) if quantity_text else 0

        # Парсим ширину
        width = None
        width_text = response.css('._select__select-width::text').get()
        if width_text:
            width_match = re.search(r'\d+', width_text)
            if width_match:
                width = float(width_match.group())

        # Получаем текущий цвет товара
        current_color = "Стандартный"

        # Ищем активный цвет по классу sz-color-block-active
        color = response.css('.sz-color-block.sz-color-block-active::attr(tooltip)').get()
        if not color:
            # Если активный класс не найден, ищем по атрибуту tooltip у всех цветов
            color = response.css('.sz-color-block::attr(tooltip)').get()

        if color:
            current_color = self.clean_text(color)

        # Добавляем цвет в название
        full_name = f"{name} ({current_color})"

        stocks = [{
            'stock': 'Санкт-Петербург',
            'quantity': quantity,
            'price': price
        }]

        return {
            'category': category,
            'product_code': self.clean_text(full_name),
            'name': full_name,
            'price': price,
            'stocks': stocks,
            'unit': unit,
            'currency': 'RUB',
            'url': response.url,
            'weight': None,
            'length': None,
            'width': width,
            'height': None
        }
