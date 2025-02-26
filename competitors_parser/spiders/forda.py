from scrapy import Request
from .base import BaseCompetitorSpider


class FordaSpider(BaseCompetitorSpider):
    """Паук для парсинга сайта forda.ru"""
    name = "forda"
    allowed_domains = ["forda.ru", "www.forda.ru"]
    start_urls = ["https://www.forda.ru/katalog/"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.processed_urls = set()  # Для отслеживания уже обработанных URL

    def parse(self, response):
        """Парсинг главной страницы каталога"""
        all_categories = response.css('a.card-header')
        links = all_categories.css('::attr(href)').getall()
        category_names = all_categories.css('::text').getall()

        for category_name, category_link in zip(category_names, links):
            category_name = self.clean_text(category_name)

            # Пропускаем ненужные категории
            if category_name not in ['Новинки', 'Распродажа']:
                self.logger.info(
                    f'Processing category: {category_name} - {category_link}'
                    )

                yield Request(
                    url=response.urljoin(category_link),
                    callback=self.parse_category,
                    cb_kwargs={'category': category_name}
                )

    def parse_category(self, response, category):
        """Парсинг страницы категории"""
        # Если это страница товара, обрабатываем её
        if response.css('h1::text').get():
            try:
                # Создаем простой объект товара без обращения к API
                product_name = self.clean_text(response.css('h1::text').get())
                if product_name:
                    product_id = self._extract_product_id(response)
                    price = self._extract_price_from_response(response)

                    yield {
                        'category': category,
                        'product_code': product_id,
                        'name': product_name,
                        'price': price,
                        'stocks': [{
                            'stock': 'Москва',
                            'quantity': 0,
                            'price': price
                        }],
                        'unit': 'шт',
                        'currency': 'RUB',
                        'url': response.url,
                        'weight': None,
                        'length': None,
                        'width': None,
                        'height': None
                    }
            except Exception as e:
                self.logger.error(
                    f"Error parsing product {response.url}: {str(e)}"
                    )

        # Находим ссылки на другие товары
        products_table = response.xpath('//*[@class="catalog-section card"]')

        for product_url in products_table.css('a::attr(href)').getall():
            product_url = response.urljoin(product_url)

            # Проверяем, не обрабатывали ли мы уже этот URL
            if product_url not in self.processed_urls:
                self.processed_urls.add(product_url)

                self.logger.info(f'Found product: {product_url}')

                yield Request(
                    url=product_url,
                    callback=self.parse_category,
                    cb_kwargs={'category': category}
                )

    def _extract_product_id(self, response):
        """Извлечение ID товара из скриптов на странице"""
        # Пытаемся найти productId в скрипте
        script_text = response.xpath(
            '//script[contains(., "productId")]/text()'
            ).get()
        if script_text:
            try:
                start_index = script_text.find('(')
                end_index = script_text.find(')')

                if start_index != -1 and end_index != -1:
                    return script_text[start_index + 1:end_index].strip()
            except Exception as e:
                self.logger.error(f"Error extracting product ID: {str(e)}")

        try:
            # Пытаемся найти offer_id в скрипте
            offer_script = response.xpath(
                '//script[contains(., "offer_id")]/text()'
                ).get()
            if offer_script:
                start_text = 'offer_id:'
                start_index = offer_script.find(start_text)

                if start_index != -1:
                    # Извлекаем подстроку после 'offer_id:'
                    substring = offer_script[
                        start_index + len(start_text):start_index + 50
                        ]
                    # Очищаем от лишних символов
                    cleaned = self.clean_text(substring.replace("'", ''))
                    return cleaned
        except Exception as e:
            self.logger.error(f"Error extracting Offer ID: {str(e)}")

        # Если не удалось найти ID, используем часть URL
        url_parts = response.url.split('/')
        if len(url_parts) > 3:
            return url_parts[-1]

        return "unknown_id"

    def _extract_price_from_response(self, response):
        """Извлечение цены из страницы товара"""
        price_text = response.xpath(
            '//*[@class="h1 text-primary"]/text()'
            ).get()
        if price_text:
            return self.extract_price(price_text)
        return 0.0
