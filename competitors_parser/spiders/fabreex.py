from typing import Dict, Any, Optional
from scrapy.http import Response
from .base import BaseCompetitorSpider
from scrapy.spiders import Rule
from scrapy.linkextractors import LinkExtractor


class FabreexSpider(BaseCompetitorSpider):
    name = 'fabreex'
    allowed_domains = ['fabreex.ru']
    start_urls = ['https://fabreex.ru/catalog/']

    rules = (
        # Правило для обхода категорий - собираем все категории
        Rule(
            LinkExtractor(
                allow=r'/catalog/[^/]+/$',  # любая категория в каталоге
                deny=(
                    r'sort=',
                    r'/favorites/',
                    r'/compare/',
                    r'/cart/',
                    r'/personal/',
                    r'/about/',
                    r'/contacts/',
                    r'/delivery/',
                    r'/payment/',
                )
            ),
            follow=True
        ),
        # Правило для парсинга товаров
        Rule(
            LinkExtractor(
                allow=r'/product/',  # все товары
                deny=(
                    r'sort=',
                    r'/favorites/',
                    r'/compare/',
                )
            ),
            callback='parse_product'
        ),
    )

    def parse_product(self, response: Response) -> Optional[Dict[str, Any]]:
        """Парсинг страницы товара"""
        try:
            self.logger.info(f"Processing product: {response.url}")

            # Название товара (проверяем разные селекторы)
            name = (
                response.css('h1::text').get() or
                response.css('.product-title::text').get() or
                response.css('.uk-h2::text').get()
            )
            if not name:
                return None  # Пропускаем товар без названия
            name = self.clean_text(name)

            # Цена (проверяем разные селекторы)
            price_text = (
                response.css('.uk-text-lead::text').get() or
                response.css('.price::text').get() or
                response.css('div[class*="price"]::text').get()
            )
            price = self.extract_price(price_text) if price_text else 0.0

            # Наличие (проверяем разные варианты)
            stock_text = (
                response.css('div:contains("В наличии")::text').get() or
                response.css('[class*="stock"]::text').get() or
                response.css('[class*="quantity"]::text').get()
            )
            stock = 1 if stock_text and 'наличии' in stock_text.lower() else 0

            # Физические характеристики
            specs = {}
            spec_rows = response.css(
                '.specifications tr, .uk-description-list dt'
                )
            for row in spec_rows:
                key = row.css('::text').get('').strip().lower()
                value = row.css('+ dd ::text, + td ::text').get('').strip()
                if key and value:
                    specs[key] = value

            # Параметры товара
            params = {}
            for select in response.css('select'):
                select_id = select.css('::attr(id)').get('').lower()
                value = select.css('option[selected]::text').get()

                if value:
                    value = value.strip()
                    if 'плотность' in select_id or 'plotnost' in select_id:
                        params['density'] = value
                    elif 'ширина' in select_id or 'shirina' in select_id:
                        params['width'] = value
                    elif 'единиц' in select_id:
                        params['unit'] = value

            # Единица измерения
            unit = params.get('unit', 'пог.м')

            # Формируем артикул
            product_code = self.create_product_code(name, **params)

            # Получаем категорию
            category = self.get_category_from_url(response.url)

            # Формируем stocks
            stocks = [{
                'stock': 'Санкт-Петербург',  # Или другой город
                'quantity': stock,
                'price': price
            }]

            item = {
                'product_code': product_code,
                'name': name,
                'price': price,
                'stocks': stocks,
                'unit': unit,
                'currency': 'RUB',
                'weight': specs.get('вес'),
                'length': specs.get('длина'),
                'width': specs.get('ширина', params.get('width')),
                'height': specs.get('высота'),
                'category': category,
                'url': response.url
            }

            self.logger.debug(f"Extracted item: {item}")
            return item

        except Exception as e:
            self.logger.error(
                f"Error parsing product {response.url}: {str(e)}"
                )
            return None
