from typing import Any, Dict, Iterator

from scrapy import Request
from scrapy.http import Response

from .base import BaseCompetitorSpider


class ZenonSpider(BaseCompetitorSpider):
    """Паук для парсинга сайта zenonline.ru."""
    name = 'zenon'
    allowed_domains = ['zenonline.ru']
    start_urls = ['https://zenonline.ru/cat/']

    custom_settings = {
        'DOWNLOAD_TIMEOUT': 30,
        'DOWNLOAD_DELAY': 3,
        'CONCURRENT_REQUESTS': 8,
        'RETRY_ENABLED': True,
        'RETRY_TIMES': 2,
    }

    def parse(self, response: Response) -> Iterator[Request]:
        """Парсим ссылки на категории из каталога."""
        self.logger.info('Парсим ссылки на категории из каталога')

        catalog = response.css('div#catalog')
        all_category = catalog.css('div.box')

        if not all_category:
            self.logger.info('Категории не найдены')
            return

        for category in all_category:
            category_name = category.css('a::text').get()
            if category_name:
                category_name = category_name.strip()
                category_link = category.css('a::attr(href)').get()
                self.logger.info(
                    f'Найдена категория: {category_name} ({category_link})'
                    )
                yield Request(
                    url=response.urljoin(category_link),
                    callback=self.parse_sub_category,
                    cb_kwargs={'parent_category': category_name}
                )

    def parse_sub_category(
            self,
            response: Response,
            parent_category: str = ''
            ) -> Iterator[Request]:
        """Парсим ссылки на подкатегории."""
        self.logger.info(
            f'Парсим ссылки на подкатегории для {parent_category}'
            )

        sub_category = response.css('div.filter_b.filter_b_catalog')
        sub_category_links = sub_category.css(
            'li.dropdown'
        ).css('a::attr(href)').getall()

        if not sub_category_links:
            self.logger.info('Ссылки на подкатегории не найдены')
            # Если подкатегорий нет,
            # обрабатываем текущую страницу как список товаров
            yield from self.parse_product_list(response, parent_category)
            return

        for sub_category_url in sub_category_links:
            self.logger.info(f'Найдена подкатегория: {sub_category_url}')
            yield Request(
                url=response.urljoin(sub_category_url),
                callback=self.parse_product_list,
                cb_kwargs={'parent_category': parent_category}
            )

    def parse_product_list(
            self,
            response: Response,
            parent_category: str = ''
            ) -> Iterator[Request]:
        """Парсим ссылки на товары в подкатегории."""
        current_category = self._extract_category(response)

        if parent_category and current_category:
            category = f'{parent_category} > {current_category}'
        elif parent_category:
            category = parent_category
        else:
            category = current_category

        self.logger.info(
            f'Обрабатываем категорию: {category} ({response.url})'
            )

        product_list = response.css('div.content')
        product_links = product_list.css(
            'div.box'
        ).css('a::attr(href)').getall()

        if not product_links:
            self.logger.warning('Ссылки на товары в подкатегории не найдены')
            return

        self.logger.info(f'Найдено товаров: {len(product_links)}')

        for product_url in product_links:
            self.logger.info(f'Отправляем на парсинг товар: {product_url}')
            yield Request(
                url=response.urljoin(product_url),
                callback=self.parse_product,
                cb_kwargs={'category': category}
            )

        # Проверяем наличие пагинации
        next_page = response.css('div.paginator a.next::attr(href)').get()
        if next_page:
            self.logger.info(f'Переход на следующую страницу: {next_page}')
            yield Request(
                url=response.urljoin(next_page),
                callback=self.parse_product_list,
                cb_kwargs={'parent_category': parent_category}
            )

    def parse_product(
            self,
            response: Response,
            category: str = ''
            ) -> Iterator[Dict[str, Any]]:
        """Парсим карточку товара."""
        self.logger.info(f'Парсим карточку товара: {response.url}')

        try:
            product_card = response.css('div.cont_page')
            product_code = response.css(
                'div#product::attr(data-articul)'
                ).get()

            # Получаем цену товара
            price_rub = product_card.css('span.rub::text').get()
            price_kop = product_card.css('span.kop::text').get()
            price_request = product_card.css('span.manager_price::text').get()

            currency = ''
            if price_rub and price_kop:
                price = f'{price_rub}{price_kop}'
                currency = 'RUB'
            elif price_request:
                price = 0.0  # Цена по запросу устанавливается как 0
                self.logger.info(f'Цена по запросу для товара {product_code}')
            else:
                price = 0.0

            # Получаем название товара
            name = product_card.css('h1.js_c1name::text').get()
            name = self.clean_text(name) if name else ''

            # Получаем единицу измерения
            unit = response.css(
                'div.buy_wrapper-minimum'
            ).css('span.nobr::text').get() or 'шт'
            unit = self.clean_text(unit)

            # Получаем характеристики товара
            charact = response.css('div#tab-1 table.tables')
            weight = charact.xpath(
                '//td[strong[text()="Вес"]]/following-sibling::td/text()'
            ).get() or None
            weight = self.clean_text(weight) if weight else None

            length = charact.xpath(
                '//td[strong[text()="Длина"]]/following-sibling::td/text()'
            ).get() or None
            length = self.clean_text(length) if length else None

            width = charact.xpath(
                '//td[strong[text()="Ширина"]]/following-sibling::td/text()'
            ).get() or None
            width = self.clean_text(width) if width else None

            height = charact.xpath(
                '//td[strong[text()="Высота"]]/following-sibling::td/text()'
            ).get() or None
            height = self.clean_text(height) if height else None

            # Получаем информацию о складах
            stocks = []
            current_stock = response.css('div#phil_name_in_select::text').get()
            current_stock = self.clean_text(
                current_stock
                ) if current_stock else 'Основной склад'

            current_amount_raw = product_card.css(
                'div.tovar_amount span.amount::attr(data-initial_amount)'
                ).get() or '0'
            current_amount = self.extract_stock(current_amount_raw)

            try:
                price_float = self.extract_price(price)
            except (ValueError, TypeError):
                price_float = 0.0

            stocks.append({
                'stock': current_stock,
                'quantity': current_amount,
                'price': price_float
            })

            yield {
                'category': category,
                'product_code': product_code,
                'name': name,
                'stocks': stocks,
                'unit': unit,
                'currency': currency if currency else 'RUB',
                'weight': weight,
                'length': length,
                'width': width,
                'height': height,
                'url': response.url
            }

        except Exception as e:
            self.logger.error(
                f'Ошибка при обработке товара {response.url}: {str(e)}'
                )

    def _extract_category(self, response: Response) -> str:
        """Извлекаем название категории."""
        breadcrumbs = response.css('div.breadcrumbs a::text').getall()
        if len(breadcrumbs) > 1:
            return self.clean_text(breadcrumbs[-1])
        elif len(breadcrumbs) == 1:
            return self.clean_text(breadcrumbs[0])

        page_title = response.css('h1.page-title::text').get()
        if page_title:
            return self.clean_text(page_title)

        title = response.css('title::text').get()
        if title:
            parts = title.split('-')
            if len(parts) > 1:
                return self.clean_text(parts[0])

        path_parts = response.url.split('/')
        if len(path_parts) > 4:
            category_from_url = path_parts[4].replace('-', ' ').title()
            if category_from_url:
                return category_from_url

        return ''
