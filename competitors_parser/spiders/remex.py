from .base import BaseCompetitorSpider
from typing import Dict, Any, Generator
import scrapy

class RemexSpider(BaseCompetitorSpider):
    name = 'remex'
    allowed_domains = ['remex.ru']
    start_urls = ['https://www.remex.ru/catalog']

    def parse(self, response):
        """Парсинг главной страницы каталога"""
        for category in response.css('.catalog-category'):
            yield response.follow(
                category.css('a::attr(href)').get(),
                callback=self.parse_category
            )

    def parse_category(self, response):
        """Парсинг страницы категории"""
        for product in response.css('.product-item'):
            yield response.follow(
                product.css('a::attr(href)').get(),
                callback=self.parse_product
            )

        next_page = response.css('.pagination .next::attr(href)').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse_category)

    def parse_product(self, response):
        """Парсинг карточки товара"""
        yield {
            'product_code': response.css('.product-code::text').get(),
            'name': response.css('.product-name::text').get(),
            'price': self.extract_price(response.css('.price::text').get()),
            'stock': self.extract_stock(response.css('.stock::text').get()),
            'unit': response.css('.unit::text').get('шт.'),
            'currency': 'RUB'
        }
