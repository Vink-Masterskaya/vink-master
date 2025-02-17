import scrapy
from .base import BaseCompetitorSpider
from urllib.parse import urljoin
import logging


class ZenonSpider(BaseCompetitorSpider):
    name = 'zenon'
    allowed_domains = ['zenonline.ru']
    start_urls = ['https://zenonline.ru/catalog']

    def parse(self, response):
        """Парсинг каталога"""
        # Парсим все категории
        for category in response.css('.catalog-category'):
            category_url = self.get_full_url(category.css('a::attr(href)').get())
            yield scrapy.Request(
                url=category_url,
                callback=self.parse_category,
                meta={'category': category.css('a::text').get().strip()}
            )

    def parse_category(self, response):
        """Парсинг страницы категории"""
        # Парсим товары на странице
        for product in response.css('.product-item'):
            yield self.parse_product(product, response.meta.get('category'))

        # Парсим пагинацию
        next_page = response.css('.pagination .next::attr(href)').get()
        if next_page:
            yield scrapy.Request(
                url=self.get_full_url(next_page),
                callback=self.parse_category,
                meta=response.meta
            )

    def parse_product(self, product, category):
        """Парсинг данных о товаре"""
        try:
            # Извлекаем артикул из текста или имени товара
            product_code = self.clean_text(product.css('.product-code::text').get())
            if not product_code:
                # Если артикула нет, используем название как артикул
                product_code = self.clean_text(product.css('.product-name::text').get())

            # Формируем item
            item = {
                'product_code': product_code,
                'name': self.clean_text(product.css('.product-name::text').get()),
                'price': self.extract_price(product.css('.price::text').get()),
                'stock': self.extract_stock(product.css('.stock::text').get()),
                'unit': self.clean_text(product.css('.unit::text').get() or 'шт.'),
                'currency': 'RUB',
                'category': category
            }

            # Проверяем обязательные поля
            if not item['name'] or not item['product_code']:
                self.logger.warning(f"Пропущен товар из-за отсутствия обязательных полей: {item}")
                return None

            return item

        except Exception as e:
            self.logger.error(f"Ошибка при парсинге товара: {e}")
            return None
