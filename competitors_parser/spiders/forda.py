import json
import scrapy
from .base import BaseCompetitorSpider


class FordaSpider(BaseCompetitorSpider):
    """Паук для парсинга сайта forda.ru"""
    name = "forda"
    allowed_domains = ["www.forda.ru"]
    start_urls = ["https://www.forda.ru/katalog/"]

    def parse(self, response):
        """Парсинг главной страницы каталога"""
        all_categories = response.css('a.card-header')
        links = all_categories.css('a::attr(href)').getall()
        txts = all_categories.css('a::text').getall()

        for txt, category in zip(txts, links):
            if txt not in ['Новинки', 'Распродажа']:
                request = scrapy.Request(
                    url=response.urljoin(category),
                    callback=self.parse_category,
                )
                request.cb_kwargs["foo"] = txt
                request.cb_kwargs["cats"] = []
                yield request

    def parse_category(self, response, foo, cats):
        """Парсинг страницы категории"""
        products_table = response.xpath(
            '//*[@class="catalog-section card"]'
        )

        try:
            product = response.css('h1::text').get()
            if product:
                name = product.replace(
                    '\n', '').replace('\r', '').replace(
                        '\t', ''
                        ).replace('₽', '')

                # Извлекаем API ID и Offer ID
                api_id = self.get_api_id(response.xpath(
                    '//script[contains(., "productId")]/text()'
                    ).get())
                offer_id = self.get_offer_id(response.xpath(
                    '//script[contains(., "offer_id")]/text()'
                    ).get())

                self.logger.info('api_id, offer_id: %s, %s', api_id, offer_id)

                if api_id:
                    # Получаем данные о наличии товара на складах
                    request = scrapy.Request(
                        url=f'https://www.forda.ru/get_offers?id={api_id}',
                        callback=self.parse_offers_data,
                        dont_filter=True
                    )
                    request.cb_kwargs["name"] = name
                    request.cb_kwargs["foo"] = foo
                    request.cb_kwargs["offer_id"] = offer_id
                    request.cb_kwargs["api_id"] = api_id
                    request.cb_kwargs["product_url"] = response.url
                    yield request
        except Exception as e:
            self.logger.error(f"Error parsing product: {str(e)}")

        # Продолжаем обход товаров в текущей категории
        products = products_table.css('a::attr(href)').getall()
        for product in products:
            if product not in cats:
                request = scrapy.Request(
                    url=response.urljoin(product),
                    callback=self.parse_category,
                )
                request.cb_kwargs["foo"] = foo
                request.cb_kwargs["cats"] = cats
                yield request

    def parse_offers_data(
            self,
            response,
            name,
            foo,
            offer_id,
            api_id,
            product_url
            ):
        """Обработка данных о ценах и наличии товара из API"""
        try:
            # Преобразуем ответ в JSON
            data = json.loads(response.text)

            # Обрабатываем каждый товар в ответе API
            for product in data:
                # Получаем цену из первого элемента prices
                price = 0.0
                if 'prices' in product and product['prices'] and len(product['prices']) > 0:
                    price = product['prices'][0].get('price', 0.0)

                # Получаем информацию о складах
                stocks = []
                if 'restsWarehouses' in product:
                    for warehouse in product['restsWarehouses']:
                        if 'store' in warehouse and 'name' in warehouse['store']:
                            stock_name = warehouse['store']['name']
                            quantity = warehouse.get('rest', 0)

                            stocks.append({
                                'stock': stock_name,
                                'quantity': quantity,
                                'price': price
                            })

                # Если нет информации о складах, создаем запись с пустыми значениями
                if not stocks:
                    stocks = [{
                        'stock': 'Основной',
                        'quantity': 0,
                        'price': price
                    }]

                # Получаем единицу измерения
                unit = product.get('units', 'шт')

                # Создаем item
                yield {
                    'category': foo,
                    'product_code': f'{offer_id} / {api_id}' if offer_id else api_id,
                    'name': name,
                    'price': price,
                    'stocks': stocks,
                    'unit': unit,
                    'currency': 'RUB',
                    'url': product_url,
                    'weight': None,
                    'length': None,
                    'width': None,
                    'height': None
                }

        except Exception as e:
            self.logger.error(f"Error parsing API response: {str(e)}")
            # В случае ошибки создаем базовый item
            yield {
                'category': foo,
                'product_code': f'{offer_id} / {api_id}' if offer_id else api_id,
                'name': name,
                'price': 0.0,
                'stocks': [{
                    'stock': 'Основной',
                    'quantity': 0,
                    'price': 0.0
                }],
                'unit': 'шт',
                'currency': 'RUB',
                'url': product_url,
                'weight': None,
                'length': None,
                'width': None,
                'height': None
            }

    def get_api_id(self, xpath_str):
        """Извлекаем API ID из скриптов на странице"""
        if not xpath_str:
            return None

        # Находим открывающую и закрывающую скобки
        open_paren = xpath_str.find('(')
        close_paren = xpath_str.find(')')

        if open_paren != -1 and close_paren != -1:
            return xpath_str[open_paren + 1: close_paren]
        return None

    def get_offer_id(self, xpath_str):
        """Извлекаем Offer ID из скриптов на странице"""
        if not xpath_str:
            return None

        offer_id_start = xpath_str.find('offer_id:')
        if offer_id_start != -1:
            offer_id = xpath_str[offer_id_start + 11: offer_id_start + 50]
            return offer_id.replace('\n', '').replace('\r', '').replace(
                '\t', ''
                ).replace("'", '')
        return None
