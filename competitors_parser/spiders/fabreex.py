import scrapy
from typing import Dict, Any, Optional
from scrapy.http import Response
from scrapy.spiders import Rule, CrawlSpider
from scrapy.linkextractors import LinkExtractor
from .base import BaseCompetitorSpider


class FabreexSpider(BaseCompetitorSpider):
    name = 'fabreex'
    allowed_domains = ['fabreex.ru']
    start_urls = ['https://fabreex.ru/catalog/']

    rules = (
        Rule(
            LinkExtractor(
                allow=r'/catalog/[^/]+/$',
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
        Rule(
            LinkExtractor(
                allow=r'/product/',
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
        try:
            self.logger.info(f"Processing product: {response.url}")

            name = (
                response.css('h1::text').get() or
                response.css('.product-title::text').get() or
                response.css('.uk-h2::text').get()
            )
            if not name:
                return None
            name = self.clean_text(name)

            price_text = (
                response.css('.uk-text-lead::text').get() or
                response.css('.price::text').get() or
                response.css('div[class*="price"]::text').get()
            )
            price = self.extract_price(price_text) if price_text else 0.0

            quantity_input = (
                response.css(
                    'input[type="number"]::attr(value), '
                    'input#quantity_16137::attr(value)').get() or
                response.css('input.uk-quantity[type="number"]::attr(value)').get()
            )
            quantity = self.extract_stock(quantity_input) if quantity_input else 0

            if not quantity:
                quantity_text = (
                    response.css('input[id^="quantity_"]::attr(value)').get() or
                    response.css('.uk-quantity input::attr(value)').get() or
                    response.css('.quantity-input::attr(value)').get()
                )
                quantity = self.extract_stock(quantity_text) if quantity_text else 0

            self.logger.debug(
                f"Extracted quantity: {quantity} from input: "
                f"{quantity_input or quantity_text}"
            )

            specs = {}
            spec_rows = response.css('.specifications tr, .uk-description-list dt')
            for row in spec_rows:
                key = row.css('::text').get('').strip().lower()
                value = row.css('+ dd ::text, + td ::text').get('').strip()
                if key and value:
                    specs[key] = value

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

            unit_text = (
                response.css('li[data-price-name] span::text').get() or
                response.css('.price-name span::text').get() or
                response.css('[data-unit]::text').get()
            )
            unit = self.clean_text(unit_text) if unit_text else "шт."

            product_code = self.create_product_code(name, **params)
            category = self.get_category_from_url(response.url)

            stocks = [{
                'stock': 'Санкт-Петербург',
                'quantity': quantity,
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
            self.logger.error(f"Error parsing product {response.url}: {str(e)}")
            return None
