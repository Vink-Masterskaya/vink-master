import scrapy

from ..items import CompetitorsParserItem


class CatalogSpider(scrapy.Spider):
    name = "catalog"
    allowed_domains = ["remex.ru"]
    start_urls = ["https://www.remex.ru/price"]

    def parse(self, response):
        """Парсинг главной страницы каталога"""
        item = CompetitorsParserItem()
        all_categoriess = response.css('a[href^="/price/"]')
        links = all_categoriess.css('a::attr(href)').getall()
        txts = all_categoriess.css('span::text').getall()
        for txt, category in zip(txts, links):
            self.logger.info('category link ==== %s %s', txt, category)
            item['category'] = txt
            item['url'] = f'https://www.remex.ru{category}'
            yield response.follow(
                category,
                callback=self.parse_category,
                cb_kwargs=dict(item=item),
            )

    def parse_category(self, response, item):
        """Парсинг страницы категории"""
        products_table = response.xpath(
            '//*[@class="price-table price-table-images"]'
        )
        products = products_table.css('a::attr(href)').getall()
        for product in products:
            self.logger.info('product link ==== %s', product)
            yield response.follow(
                product,
                callback=self.parse_product,
                cb_kwargs=dict(item=item),
            )

    def parse_product(self, response, item):
        product_group = response.xpath('//*[@class="price-table pprtbl"]')
        items = product_group.css('td::text').getall()
        """Парсинг карточки товаров"""
        product = []
        count = 0
        for it in items:
            count += 1
            product.append(it)
            if count == 3:
                count = 0
                item['name'] = product[0]
                item['unit'] = product[1]
                item['price'] = product[2]
                item['currency'] = 'руб.'
                yield item
                self.logger.info('product ==== %s', item)
                product.clear()
