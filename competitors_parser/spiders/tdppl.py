import logging
import re
from typing import Any, Dict, Iterator, List

from playwright.sync_api import sync_playwright
from scrapy import Request
from scrapy.http import Response

from .base import BaseCompetitorSpider


class PappilonsCategoryParse:
    """
    Используется для получения ссылок на товары категорий с помощью Playwright.
    """
    def __init__(self, url: str):
        """
        Инициализация класса для парсинга категорий

        Args:
            url: URL категории товаров
        """
        self.url = url
        self.logger = logging.getLogger(self.__class__.__name__)

    def parse(self) -> List[str]:
        """
        Получает все ссылки на товары в категории с использованием Playwright

        Returns:
            List[str]: Список ссылок на товары
        """
        links = []
        try:
            with sync_playwright() as playwright:
                self.logger.info(f'Запуск Playwright для URL: {self.url}')
                browser = playwright.chromium.launch(headless=True)
                context = browser.new_context()
                page = context.new_page()
                i = 1

                while True:
                    pagination_url = f'{self.url}?PAGEN_1={i}&AJAX=Y'
                    self.logger.info(
                        f'Обработка страницы пагинации: {pagination_url}'
                        )
                    page.goto(pagination_url)

                    # Получаем ссылки на товары с текущей страницы
                    stickers = page.locator('.product-card-inner__stickers')
                    new_links = stickers.evaluate_all(
                        'elements => elements.map(element => element.href)'
                        )

                    # Проверяем, не дошли ли мы до конца пагинации
                    if not new_links:
                        self.logger.info(
                            f'Пустая страница пагинации: {pagination_url}'
                            )
                        break

                    if new_links and new_links[0] in links:
                        self.logger.info(
                            f'Достигнут конец пагинации на странице {i}'
                            )
                        break
                    else:
                        self.logger.info(
                            f'Найдено {len(new_links)} товаров на странице {i}'
                            )
                        links.extend(new_links)
                        i += 1

                page.close()
                context.close()
                browser.close()

                self.logger.info(
                    f'Всего собрано {len(links)} ссылок на товары'
                    )
                return links
        except Exception as e:
            self.logger.error(
                f'Ошибка при парсинге категории {self.url}: {str(e)}'
                )
            return links


class TdpplSpider(BaseCompetitorSpider):
    name = 'tdppl'
    allowed_domains = ['tdppl.ru']
    start_urls = ['https://tdppl.ru/catalog/']

    # Настройки специальных экспортеров для Playwright
    custom_settings = {
        'ITEM_PIPELINES': {
            'competitors_parser.pipelines.validation.ValidationPipeline': 300,
            'competitors_parser.exporters.playwright_csv_exporter.PlaywrightCSVExporter': 400,
            'competitors_parser.exporters.playwright_json_exporter.PlaywrightJSONExporter': 500,
        }
    }

    def parse(self, response: Response) -> Iterator[Request]:
        """Парсинг главной страницы каталога."""
        # Получаем ссылки на категории и их названия
        categories = response.css('a.block_main_left_menu__link')

        for category in categories:
            category_name = category.css('::attr(title)').get('').strip()
            category_url = category.css('::attr(href)').get()

            if not category_url:
                continue

            self.logger.info(
                f'Обнаружена категория: {category_name} ({category_url})'
                )

            yield Request(
                url=response.urljoin(category_url),
                callback=self.parse_category,
                cb_kwargs={'category': category_name}
            )

    def parse_category(
            self,
            response: Response,
            category: str
            ) -> Iterator[Request]:
        """Парсинг страницы категории."""
        self.logger.info(f'Обработка категории: {category} ({response.url})')

        # Используем Playwright для получения ссылок на товары
        product_links = PappilonsCategoryParse(response.url).parse()

        # Обрабатываем каждую ссылку на товар
        for product_url in product_links:
            self.logger.info(
                f'Обнаружен товар в категории {category}: {product_url}'
                )

            yield Request(
                url=product_url,
                callback=self.parse_product,
                cb_kwargs={'category': category}
            )

    def parse_product(
            self,
            response: Response,
            category: str
            ) -> Iterator[Dict[str, Any]]:
        """Парсинг страницы товара."""
        try:
            self.logger.info(f'Обработка товара: {response.url}')

            # Получаем код товара
            product_code = response.css(
                'div.product_detail_info_block__article span:nth-child(2)::text'
                ).get('')
            product_code = self.clean_text(product_code)

            # Получаем название товара
            name = response.css('h1.product_detail_title::text').get('')
            name = self.clean_text(name)

            # Получаем информацию о складах из скрипта
            script_content = response.xpath(
                '//div[@class="product_detail_info_block__line"]//script/text()'
            ).get('')

            stocks = self._extract_stocks(script_content)

            # Получаем цену и валюту
            price_text = response.css(
                'span.product_card__block__new_price_product::text'
                ).get('')
            price, currency = self._extract_price_and_currency(price_text)

            # Получаем единицу измерения
            unit = response.css(
                'span.product_card__block_buy_measure::text'
                ).get('')
            unit = self.clean_text(unit) if unit else 'шт'

            # Устанавливаем цену для всех складов
            for stock in stocks:
                stock['price'] = price

            # Формируем и возвращаем item
            yield {
                'category': category,
                'product_code': product_code,
                'name': name,
                'price': price,
                'stocks': stocks,
                'unit': unit,
                'currency': currency,
                'url': response.url
            }

        except Exception as e:
            self.logger.error(
                f'Ошибка при обработке товара {response.url}: {str(e)}'
                )

    def _extract_stocks(self, script_content: str) -> List[Dict[str, Any]]:
        """
        Извлекает информацию о наличии товара на складах из скрипта.

        Args:
            script_content: Содержимое скрипта с информацией о складах.

        Returns:
            List[Dict[str, Any]]: Список с информацией о складах.
        """
        stocks = []

        if not script_content:
            return stocks

        try:
            # Извлекаем названия городов
            pattern_city = r'data-store-selector="name">(.*?)<'
            match_city = re.findall(pattern_city, script_content)
            match_city = match_city[:len(match_city) // 2]

            # Извлекаем информацию о наличии
            pattern_stock = r'data-store-selector="quantity" (.*?)<'
            match_stock = re.findall(pattern_stock, script_content)
            match_stock = match_stock[:len(match_stock) // 2]

            # Преобразуем значения наличия в читаемый формат и количество
            match_stock_corrected = []
            for stock in match_stock:
                if 'many' in stock:
                    quantity = 10  # Примерное количество, если "В наличии"
                else:
                    quantity = 0
                match_stock_corrected.append(quantity)

            # Формируем список складов в нужном формате
            for city, quantity in zip(match_city, match_stock_corrected):
                stocks.append({
                    'stock': city,
                    'quantity': quantity,
                    'price': 0.0  # Цена будет установлена позже
                })

        except Exception as e:
            self.logger.error(
                f'Ошибка при извлечении информации о складах: {str(e)}'
                )

        return stocks

    def _extract_price_and_currency(self, price_text: str) -> tuple:
        """
        Извлекает цену и валюту из текста.

        Args:
            price_text: Текст, содержащий цену и валюту.

        Returns:
            tuple: (цена(float), валюта(str)).
        """
        if not price_text:
            return 0.0, 'RUB'

        try:
            # Очищаем текст от неразрывных пробелов
            price_text = price_text.replace('\xa0', '').strip()

            # Разделяем на цену и валюту
            parts = price_text.split()
            if len(parts) >= 2:
                price_str = parts[0]
                currency = parts[1]

                # Преобразуем цену в число
                price = self.extract_price(price_str)

                # Стандартизируем валюту
                if currency in ['р.', 'руб.', 'руб', 'р']:
                    currency = 'RUB'

                return price, currency
            else:
                # Если не удалось разделить, пробуем извлечь только цену
                price = self.extract_price(price_text)
                return price, 'RUB'

        except Exception as e:
            self.logger.error(
                f"Ошибка при извлечении цены и валюты из '{price_text}': {str(e)}"
                )
            return 0.0, 'RUB'
