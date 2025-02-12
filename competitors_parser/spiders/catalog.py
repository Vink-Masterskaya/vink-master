import scrapy
import logging


logger = logging.getLogger(__name__)

class CatalogSpider(scrapy.Spider):
    name = "catalog"
    allowed_domains = ["remex.ru"]
    start_urls = ["https://www.remex.ru/price"]


    def parse(self, response):
        """Парсинг главной страницы каталога"""
        main_menu = response.xpath('//*[@class="directions directions--new"]')
        logger.info('main_selector ===== %s', main_menu)
        categories = main_menu.css('a::attr(href)').getall()

        for category in categories:
            if '/price/' in category:
                logger.info('category link ==== %s', category)
                yield response.follow(
                    category,
                    callback=self.parse_category,
                )


    def parse_category(self, response):
        """Парсинг страницы категории"""
        products_table = response.xpath('//*[@class="price-table price-table-images"]')
        products = products_table.css('a::attr(href)').getall()
        for product in products:
            logger.info('product link ==== %s', product)
            yield response.follow(
                product,
                callback=self.parse_product
            )

        next_page = response.css('.pagination .next::attr(href)').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse_category)

    def parse_product(self, response):
        product_group = response.xpath('//*[@class="price-table pprtbl"]')
        items = product_group.css('th::text').getall()
        """Парсинг карточки товаров"""
        product = []
        count = 0
        for item in items:
            count += 1
            logger.info('item ==== %s %s', count, item)
#            if item not in ['Наименование', 'Ед.изм.', 'Цена, руб.']:
#            product.append(item)
            logger.info('=============== %s', product)
            yield {
#                'product_code': response.css('.product-code::text').get(),
                'name': item,
#                'price': product[2],
#                'stock': self.extract_stock(response.css('.stock::text').get()),
#                'unit': product[1],
#                'currency': 'RUB'
            }
            # if count == 3:
            #     count = 0 
            logger.info('product %s ====', product)
            product.clear()
