import scrapy
import requests
from ..items import CompetitorsParserItem

item = CompetitorsParserItem()
cats = []


class CatalogSpider(scrapy.Spider):
    name = "forda"
    allowed_domains = ["www.forda.ru"]
    start_urls = ["https://www.forda.ru/katalog/"]

    async def parse(self, response):
        """Парсинг главной страницы каталога"""
        all_categories = response.css('a.card-header')
        links = all_categories.css('a::attr(href)').getall()
        txts = all_categories.css('a::text').getall()
        for txt, category in zip(txts, links):
            if txt not in ['Новинки', 'Распродажа']:
                id = 0
                item['id'] = id
                request = scrapy.Request(
                    url=response.urljoin(category),
                    callback=self.parse_category,
                )
                # print('category ------ ', category)
                request.cb_kwargs["foo"] = txt
                request.cb_kwargs["cats"] = cats
                yield request

    async def parse_category(self, response, foo, cats):
        """Парсинг страницы категории"""
        print('category ------ ', response.request.url)
        try:
            api_id = get_api_id(
                    response.xpath(
                        '//script[contains(., "productId")]/text()'
                    ).get()
            )
            product = response.css('h1::text').get()
            name = product.replace(
                '\n', '').replace('\r', '').replace('\t', '').replace('₽', '')
            print('try________', product, api_id)
            api_id = get_api_id(
                response.xpath(
                    '//script[contains(., "productId")]/text()'
                ).get()
            )
            offer_id = get_offer_id(
                response.xpath(
                    '//script[contains(., "offer_id")]/text()'
                ).get()
            )
            self.logger.info(
                'api_id, offer_id_________%s, %s ', api_id, offer_id
            )
            stocks = await get_stocks(api_id)
            for stock in stocks:
                item['category'] = foo
                item['product_code'] = f'{offer_id} / {api_id}'
                item['id'] = item['id'] + 1
                item['url'] = response.request.url
                item['price'] = stock['price']
                item['name'] = f'{name}{stock["name"]}'
                item['stocks'] = stock['stocks']
                yield item
        except Exception as e:
            print(e)
        products_table = response.xpath(
            '//*[@class="catalog-section card"]'
        )
        products = products_table.css('a::attr(href)').getall()
        for product in products:
            if product not in cats:
                self.logger.info('category ========= %s', foo)
                self.logger.info('category link ========= %s', product)
                request = scrapy.Request(
                    url=response.urljoin(product),
                    callback=self.parse_category,
                )
                request.cb_kwargs["foo"] = foo
                request.cb_kwargs["cats"] = cats
                yield request


def get_api_id(xpath_str: str) -> str:
    return (xpath_str[xpath_str.find('(') + 1: xpath_str.find(')')])


def get_offer_id(xpath_str: str) -> str:
    return (
        xpath_str[
            xpath_str.find('offer_id:') + 11: xpath_str.find('offer_id:') + 50
        ]
        .replace('\n', '').replace('\r', '').replace('\t', '').replace("'", '')
    )


async def get_stocks(api_id: str):
    url = f'https://www.forda.ru/get_offers?id={api_id}'
    response = requests.get(url).json()
    resp = []
    resp_json = {}
    for product in response:
        resp_json['name'] = product['name'],
        resp_json['price'] = product['prices'][0]['price']
        stocks = []
        for warehouse in product['restsWarehouses']:
            stocks.append({
                'stock': warehouse['store']['name'],
                'quantity': warehouse['rest'],
                'price': product['prices'][0]['price']}
            )
        resp_json['stocks'] = stocks
        resp.append(resp_json.copy())
    print(resp)
    print('----------------------------')
    return resp
