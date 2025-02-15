import scrapy

from ..items import CompetitorsParserItem

item = CompetitorsParserItem()


class CatalogSpider(scrapy.Spider):
    name = "fabreex"
    allowed_domains = ["fabreex.ru"]
    start_urls = ["https://www.fabreex.ru/catalog"]

    def parse(self, response):
        """Парсинг главной страницы каталога"""
        all_categories = response.css('.uk-button')
        links = all_categories.css('a::attr(href)').getall()
        txts = all_categories.css('a::text').getall()
        for txt, category in zip(txts, links):
            self.logger.info('category link ==== %s %s', txt, category)
            self.logger.info(
                'category link ==== %s',
                txt.replace('\n', '').replace('\r', '').replace('\t', '')
            )
            id = 0
            item['id'] = id
            request = scrapy.Request(
                url=response.urljoin(category),
                callback=self.parse_category,
            )
            request.cb_kwargs["foo"] = txt.replace(
                '\n', '').replace('\r', '').replace('\t', '')
            yield request

    def parse_category(self, response, foo):
        """Парсинг страницы категории"""
        products_table = response.xpath(
            '//*[@class="sz-cards-bottom sz-cards-bottom-new"]'
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
        product = response.css('h1::text').get()
        price = response.css('.sz-full-price-prod::text').get()
        units = list(
            response.css('uk-position-relative uk-position-z-index').getall())
        char_key = response.xpath(
            '//*[@class="sz-text-large"]/text()'
        ).getall()
        char_value = response.xpath(
            '//*[@class="sz-text-large"]/following-sibling::div[1]/text()'
        ).getall()
        char = list(zip(char_key, char_value))
        item['category'] = foo
        item['id'] = item['id'] + 1
        item['url'] = response.request.url
        item['name'] = product.replace(
            '\n', '').replace('\r', '').replace('\t', '').replace('₽', '')
        item['unit'] = units
        item['price'] = price.replace(
            '\n', '').replace('\r', '').replace('\t', '').replace('₽', '')
        item['currency'] = 'руб.'
        item['unit'] = char
        yield item

        self.logger.info('item +++++ %s', item)
