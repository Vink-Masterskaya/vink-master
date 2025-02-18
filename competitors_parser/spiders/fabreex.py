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

    # Маппинг категорий по id из меню
    CATEGORY_MAP = {
        '117': 'Аксессуары',
        '179': 'Бумага',
        '177': 'Негорючие ткани для интерьера',
        '181': 'Оборудование',
        '180': 'Сублимационные чернила',
        '178': 'Ткани для печати',
        '176': 'Трикотаж'
    }

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

    def get_category_from_menu(self, response: Response) -> str:
        """Получение категории по тексту и атрибуту name из меню"""
        # Сначала пробуем получить name атрибут
        menu_item = response.css('.burger-menu__main-left-item::attr(name)').get()
        category = self.CATEGORY_MAP.get(menu_item, '')

        if not category:
            # Если не получилось по name, пробуем по тексту ссылки
            menu_items = response.css('.burger-menu__main-left-item::text').getall()
            menu_items = [self.clean_text(item) for item in menu_items if item.strip()]

            # Проверяем URL на наличие ключевых слов категорий
            url = response.url.lower()
            if 'plotter' in url or 'printer' in url:
                category = 'Оборудование'
            elif 'chernila' in url:
                category = 'Сублимационные чернила'
            elif 'bumaga' in url:
                category = 'Бумага'
            elif 'tkan' in url:
                category = 'Ткани для печати'
            elif 'aksessuar' in url:
                category = 'Аксессуары'
            else:
                # Если не нашли по URL, пробуем определить по названию товара
                product_name = self.clean_text(response.css('h1::text').get() or '').lower()
                if 'плоттер' in product_name or 'принтер' in product_name:
                    category = 'Оборудование'
                elif 'чернила' in product_name:
                    category = 'Сублимационные чернила'
                else:
                    category = "Другое"

        self.logger.debug(f"Category detection: name={menu_item}, url={response.url}, category={category}")
        return category

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

            # Наличие и количество
            quantity_input = response.css('input[type="number"]::attr(max)').get()
            quantity = self.extract_stock(quantity_input) if quantity_input else 0

            if not quantity:
                quantity_text = (
                    response.css('input[id^="quantity_"]::attr(max)').get() or
                    response.css('.uk-quantity input::attr(max)').get() or
                    response.css('.quantity-input::attr(max)').get()
                )
                quantity = self.extract_stock(quantity_text) if quantity_text else 0

            self.logger.debug(
                f"Extracted quantity: {quantity} from input: "
                f"{quantity_input or quantity_text}"
            )

            # Физические характеристики
            specs = {}
            weight_text = response.css('input[type="number"]::attr(max)').get()
            specs['вес'] = weight_text if weight_text else None

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

            # Получаем категорию
            category = self.get_category_from_menu(response)
            self.logger.debug(f"Found category by menu item name: {category}")

            stocks = [{
                'stock': 'Санкт-Петербург',
                'quantity': quantity,
                'price': price
            }]

            item = {
                'category': category,
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
                'url': response.url
            }

            self.logger.debug(f"Extracted item: {item}")
            return item

        except Exception as e:
            self.logger.error(f"Error parsing product {response.url}: {str(e)}")
            return None
