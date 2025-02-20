from typing import Dict, Any, Iterator
from scrapy import Request
from scrapy.http import Response
from .base import BaseCompetitorSpider


class FabreexSpider(BaseCompetitorSpider):
    name = 'fabreex'
    allowed_domains = ['fabreex.ru']
    start_urls = ['https://fabreex.ru/catalog/']

    def parse(self, response: Response) -> Iterator[Request]:
        """Парсинг главной страницы каталога"""
        all_categories = response.css('.uk-button')
        links = all_categories.css('a::attr(href)').getall()
        categories = all_categories.css('a::text').getall()

        for category_name, category_link in zip(categories, links):
            category = self.clean_text(category_name)
            self.logger.info(
                f'Category link: {category} - {category_link}'
            )

            yield Request(
                url=response.urljoin(category_link),
                callback=self.parse_category,
                cb_kwargs={'category': category}
            )

    def parse_category(
        self, response: Response, category: str
    ) -> Iterator[Request]:
        """Парсинг страницы категории"""
        products_table = response.xpath(
            '//*[@class="sz-cards-bottom sz-cards-bottom-new"]'
        )
        self.logger.info(f'Processing category: {category}')

        products = products_table.css('a::attr(href)').getall()
        for product_url in products:
            self.logger.info(f'Product link: {product_url}')
            yield Request(
                url=response.urljoin(product_url),
                callback=self.parse_product,
                cb_kwargs={'category': category}
            )

        next_page = response.css(
            '.uk-pagination .uk-active + li a::attr(href)'
        ).get()
        if next_page:
            self.logger.info(f'Next page link: {next_page}')
            yield Request(
                url=response.urljoin(next_page),
                callback=self.parse_category,
                cb_kwargs={'category': category}
            )

    def parse_product(
            self,
            response: Response,
            category: str
            ) -> Iterator[Dict[str, Any]]:
        """Парсинг страницы товара"""
        try:
            name = response.css('h1::text').get()
            if not name:
                return
            name = self.clean_text(name)

            price_text = response.css('.sz-full-price-prod::text').get()
            price = self.extract_price(price_text) if price_text else 0.0

            # Получаем текущий цвет
            color = response.xpath(
                '//*[@class="sz-color-block sz-color-block-active"]'
                )
            current_color = color.css('a::attr(uk-tooltip)').get()
            current_color = self.clean_text(
                current_color
                ) if current_color else "Стандартный"

            yield self._create_item(
                name=name,
                price=price,
                category=category,
                response=response,
                current_color=current_color
            )

            # Перебираем ссылки на другие цвета
            color_links = response.css(
                '.desc-color-element::attr(href)'
                ).getall()

            for color_link in color_links:
                if color_link:
                    yield Request(
                        url=response.urljoin(color_link),
                        callback=self.parse_product,
                        cb_kwargs={'category': category}
                    )

        except Exception as e:
            self.logger.error(
                f"Error parsing product {response.url}: {str(e)}"
                )

    def _create_item(
            self,
            name: str,
            price: float,
            category: str,
            response: Response,
            current_color: str
            ) -> Dict[str, Any]:
        """Создание item'а с общими параметрами"""
        # Парсим юнит
        units = response.xpath(
            '//*[@class="uk-position-relative uk-position-z-index"]'
            '/text()'
        ).getall()[:2]

        if units:
            if all(unit.strip() == 'За шт.' for unit in units):
                unit = 'За шт.'
            else:
                unit = [unit.strip() for unit in units]
        else:
            unit = 'За шт.'

        # Парсим количество
        quantity_text = response.css('input[type="number"]::attr(max)').get()
        quantity = self.extract_stock(quantity_text) if quantity_text else 0

        # Парсим ширину и форматируем
        width = None
        width_value = response.css(
            '.sz-text-count-select.sz-text-count-select-active::text'
            ).get()

        if width_value:
            width = f"См: {width_value.strip()}"

        # Формируем название с цветом
        full_name = f"{name} ({current_color})"

        stocks = [{
            'stock': 'Санкт-Петербург',
            'quantity': quantity,
            'price': price
        }]

        return {
            'category': category,
            'product_code': self.clean_text(full_name),
            'name': full_name,
            'price': price,
            'stocks': stocks,
            'unit': unit,
            'currency': 'RUB',
            'url': response.url,
            'weight': None,
            'length': None,
            'width': width,
            'height': None
        }
