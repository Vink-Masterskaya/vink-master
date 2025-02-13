import scrapy

from ..items import CompetitorsParserItem

item = CompetitorsParserItem()


class CatalogSpider(scrapy.Spider):
    name = "remex"
    allowed_domains = ["remex.ru"]
    start_urls = ["https://www.remex.ru/price"]

    def parse(self, response):
        """Парсинг главной страницы каталога"""
        all_categories = response.css('a[href^="/price/"]')
        links = all_categories.css('a::attr(href)').getall()
        txts = all_categories.css('span::text').getall()
        for txt, category in zip(txts, links):
            self.logger.info('category link ==== %s %s', txt, category)
            id = 0
            item['id'] = id
            request = scrapy.Request(
                url=response.urljoin(category),
                callback=self.parse_category,
            )
            if txt == 'мобильные':
                txt = 'мобильные стенды'
            if txt == 'стенды':
                txt = 'Инструменты, крепёж'
            request.cb_kwargs["foo"] = txt
            yield request

    def parse_category(self, response, foo):
        """Парсинг страницы категории"""
        products_table = response.xpath(
            '//*[@class="price-table price-table-images"]'
        )
        self.logger.info('category ------ %s', foo)
        products = products_table.css('a::attr(href)').getall()
        for product in products:
            self.logger.info('product link ==== %s', product)
            request = scrapy.Request(
                url=response.urljoin(product),
                callback=self.parse_product,
            )
            request.cb_kwargs["foo"] = foo
            yield request

    def parse_product(self, response, foo):
        """Парсинг карточки товаров"""
        product_group = response.xpath('//*[@class="price-table pprtbl"]')
        items = product_group.css('td::text').getall()
        product = []
        count = 0
        for it in items:
            count += 1
            product.append(it)
            if count == 3:
                count = 0
                item['category'] = foo
                item['id'] = item['id'] + 1
                item['url'] = response.request.url
                item['name'] = product[0]
                item['unit'] = product[1]
                item['price'] = product[2]
                item['currency'] = 'руб.'
                yield item
                product.clear()
