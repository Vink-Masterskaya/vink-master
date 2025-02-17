from .base import BaseCompetitorSpider
from scrapy import Request


class FabreexSpider(BaseCompetitorSpider):
    name = 'fabreex'
    allowed_domains = ['fabreex.ru']
    start_urls = ['https://fabreex.ru/catalog']

    def parse(self, response):
        """Парсинг каталога категорий"""
        # Парсим все категории на странице
        categories = response.css('.bx_catalog_tile_section a')
        for category in categories:
            category_url = self.get_full_url(category.css('::attr(href)').get())
            category_name = category.css('::text').get()

            yield Request(
                url=category_url,
                callback=self.parse_category,
                meta={
                    'category': self.clean_text(category_name)
                }
            )

    def parse_category(self, response):
        """Парсинг страницы категории с товарами"""
        # Парсим товары на текущей странице
        products = response.css('.product-item')

        for product in products:
            # Получаем ссылку на товар для парсинга детальной информации
            product_url = self.get_full_url(
                product.css('.product-item-title a::attr(href)').get()
            )

            yield Request(
                url=product_url,
                callback=self.parse_product,
                meta={
                    'category': response.meta.get('category')
                }
            )

        # Проверяем наличие следующей страницы
        next_page = response.css('.bx-pagination-next a::attr(href)').get()
        if next_page:
            yield Request(
                url=self.get_full_url(next_page),
                callback=self.parse_category,
                meta=response.meta
            )

    def parse_product(self, response):
        """Парсинг страницы товара"""
        try:
            # Парсим основную информацию о товаре
            name = response.css('.product-item-detail-tab-content h1::text').get()
            price_text = response.css('.product-item-detail-price-current::text').get()
            stock_text = response.css('.product-item-detail-available::text').get()

            # Пытаемся получить артикул
            product_code = response.css('[data-entity="sku-line-block"] .product-item-detail-properties-value::text').get()

            # Если артикул не найден, используем часть URL
            if not product_code:
                product_code = response.url.split('/')[-2]

            # Формируем item
            item = {
                'product_code': self.clean_text(product_code),
                'name': self.clean_text(name),
                'price': self.extract_price(price_text),
                'stock': self.extract_stock(stock_text),
                'unit': 'шт.',  # По умолчанию
                'currency': 'RUB',
                'category': response.meta.get('category'),
                'url': response.url
            }

            # Проверяем обязательные поля
            if item['name'] and (item['product_code'] or item['name']):
                yield item
            else:
                self.logger.warning(
                    f"Пропущен товар из-за отсутствия обязательных полей: {response.url}"
                )

        except Exception as e:
            self.logger.error(
                f"Ошибка при парсинге товара {response.url}: {str(e)}"
            )
