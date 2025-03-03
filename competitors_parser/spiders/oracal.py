import scrapy
from time import sleep
from scrapy.spiders import Spider
import json


base_prod_list_url = 'https://api.oracal-online.ru/api/product/category?page=1&slug='
base_prod_url_begin = 'https://api.oracal-online.ru/api/product-offer/list?slug='
base_prod_url_end = '&page=1&isAvailable=false'
base_subcat_url = 'https://api.oracal-online.ru/api/category?slug='


class QuoteCrawlSpider(Spider):
    name = 'oracal'
    allowed_domains = ['oracal-online.ru']
    start_urls = ['https://api.oracal-online.ru/api/category/list/']

    async def parse(self, response):
        result = json.loads(response.body)
        for category in result['data']:
            subcats = category['subCategory']
            # print('===', category['id'], category['slug'])
            for sub in subcats:
                sleep(0.1)
                # print('--------', sub['id'], sub['slug'])
                url = f'{base_subcat_url}{sub["slug"]}'
                request = scrapy.Request(
                    url=url,
                    callback=self.parse_category,
                )
                request.cb_kwargs['cat'] = f'{category["title"]} - {sub["title"]}'
                request.cb_kwargs['sub'] = sub["slug"]
                yield request

    async def parse_category(self, response, cat, sub):
        result = json.loads(response.body)
        data = result['data']['subCategories']        
        if len(data):
            for sub in data:
                sleep(0.3)
                # print('рекурсия', sub["slug"])
                url = f'{base_subcat_url}{sub["slug"]}'
                request = scrapy.Request(
                    url=url,
                    callback=self.parse_category,
                )
                request.cb_kwargs['cat'] = cat
                request.cb_kwargs['sub'] = sub
                yield request
        else:
            sleep(0.3)
            # print('-----------Базовый случай')
            url = f'{base_prod_list_url}{sub}'
            request = scrapy.Request(
                url=url,
                callback=self.parse_product_list,
            )
            request.cb_kwargs['cat'] = cat
            yield request

    async def parse_product_list(self, response, cat):
        result = json.loads(response.body)
        for product in result['data']:
            sleep(0.3)
            url_prod = f'{base_prod_url_begin}{product["slug"]}{base_prod_url_end}'
            request = scrapy.Request(
                    url=url_prod,
                    callback=self.parse_product,
            )
            request.cb_kwargs['cat'] = f'{cat} --- {product["title"]}'
            yield request

    async def parse_product(self, response, cat):
        result = json.loads(response.body)
        print('!!!', cat)
        data = result['data']['offers']['data']
        for product in data:
            sleep(0.5)
            print(cat, '-------', product['id'], product['title'],)
            price = get_price(product)
            stocks = get_stocks(product)
            yield {
                'category': cat,
                'product_code': f'{product["id_1s"]}/{product["id"]}',
                'name': product['title'],
                'price': price,
                'stocks': stocks,
                'url': response.request.url,
                'unit': product['unit'],
                'weight': product['weight'],                
                'color': product['properties'][0]['value'],
                'width': product['properties'][1]['value'],
                'length': product['properties'][2]['value']
            }


def get_price(product):
    # три цены
    prices = []
    for item in product["prices"]: 
        prices.append(
            {
                'price': item["price"],
                'unit': item["unit"] 
            }
        )
    print(prices)
    return prices


def get_stocks(product):
    # два стокс москва и остальные
    moscow_stock = []
    other_stock= []
    for moscow in product['restsAvailable']:
        moscow_stock.append(
            {
                'quantity': moscow['amount'],
                'unit': moscow['title']
            }
        )
        
    for other in product['restsAllStore']:
        other_stock.append(
            {
                'quantity': other['amount'],
                'unit': other['title']
            }
    )
    print([{'stock': 'Москва', 'rest': moscow_stock}, {'stock': 'Другие', 'rest': other_stock}])
    return [{'stock': 'Москва', 'rest': moscow_stock}, {'stock': 'Другие', 'rest': other_stock}]
