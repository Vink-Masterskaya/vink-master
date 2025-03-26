# Архитектура проекта парсера данных конкурентов

## Обзор проекта

Проект представляет собой систему для парсинга данных о товарах с сайтов конкурентов. Архитектура основана на фреймворке Scrapy с дополнительными модулями для обработки данных, включая поддержку сложных веб-сайтов с динамическим контентом через Playwright.

## Структура проекта

```
vink_master/                      # Корневая директория проекта
├── competitors_parser/           # Основной код
│   ├── __init__.py
│   ├── items.py                  # Определение структуры данных
│   ├── middlewares.py            # Middleware для Scrapy
│   ├── settings.py               # Настройки Scrapy
│   │
│   ├── exporters/                # Экспортеры данных
│   │   ├── __init__.py
│   │   ├── base.py               # Базовый класс экспортера
│   │   ├── csv_exporter.py       # Экспортер CSV
│   │   ├── json_exporter.py      # Экспортер JSON
│   │   ├── playwright_csv_exporter.py   # Экспортер CSV для Playwright
│   │   └── playwright_json_exporter.py  # Экспортер JSON для Playwright
│   │
│   ├── spiders/                  # Пауки для парсинга
│   │   ├── __init__.py
│   │   ├── base.py               # Базовый паук
│   │   ├── fabreex.py            # Паук для fabreex.ru
│   │   ├── remex.py              # Паук для remex.ru
│   │   ├── zenon.py              # Паук для zenonline.ru
│   │   ├── forda.py              # Паук для forda.ru
│   │   ├── tdppl.py              # Паук для tdppl.ru
│   │   └── oracal.py             # Паук для oracal-online.ru
│   │
│   ├── pipelines/               
│   │   ├── __init__.py
│   │   └── validation.py         # Пайплайн валидации
│   │
│   └── utils/                    # Утилиты
│       ├── __init__.py
│       └── config.py             # Конфигурация
│
├── data/                         # Данные (игнорируется git)
│   ├── processed/                # Обработанные данные
│   │   ├── fabreex/              # Данные для каждого паука
│   │   ├── remex/
│   │   ├── zenon/
│   │   └── ...
│   └── .gitkeep
│
├── logs/                         # Логи (игнорируется git)
│   └── .gitkeep
│
└── scripts/                      # Скрипты
    └── start_parser.py           # Запуск парсера
```

## Ключевые компоненты архитектуры

### 1. Парсеры (Spiders)

Парсеры отвечают за обход веб-сайтов и извлечение данных. Проект использует фреймворк Scrapy для этой задачи.

#### Базовый паук (`BaseCompetitorSpider`)

Все пауки наследуются от базового класса `BaseCompetitorSpider`, который предоставляет общую функциональность:

- Методы очистки и извлечения данных (цены, количество на складе)
- Логирование и обработка ошибок
- Обработка общих сценариев (цена по запросу, форматирование URL)

#### Специфические пауки

Каждый паук настроен для конкретного сайта конкурента:

- **FabreexSpider**: парсинг HTML-страниц fabreex.ru
- **RemexSpider**: парсинг HTML-страниц remex.ru
- **ZenonSpider**: парсинг HTML-страниц zenonline.ru с пагинацией
- **FordaSpider**: парсинг с использованием API forda.ru
- **TdpplSpider**: парсинг с использованием Playwright для сайта с динамическим контентом
- **OracalSpider**: парсинг API сайта oracal-online.ru

### 2. Обработка данных (Pipelines)

#### Валидация (`ValidationPipeline`)

Пайплайн валидации обеспечивает приведение данных к единому формату:

- Проверка обязательных полей
- Нормализация типов данных
- Стандартизация структуры информации о складах
- Обработка различных форматов единиц измерения

Пайплайн преобразует разнородные данные с разных сайтов в унифицированный формат для дальнейшей обработки.

### 3. Экспорт данных (Exporters)

Компоненты для сохранения данных в различных форматах.

#### Базовый экспортер (`BaseExporter`)

Предоставляет общую функциональность:
- Создание директорий для экспорта
- Генерация имен файлов с временными метками
- Базовые методы для открытия/закрытия файлов

#### Стандартные экспортеры

- **CSVExporter**: экспорт данных в CSV формат
- **JSONExporter**: экспорт данных в JSON формат

#### Специализированные экспортеры для Playwright

- **PlaywrightCSVExporter**: экспорт в CSV из пауков, использующих Playwright
- **PlaywrightJSONExporter**: экспорт в JSON из пауков, использующих Playwright

### 4. Middleware

**ErrorHandlerMiddleware** отвечает за обработку и логирование ошибок при запросах:
- Логирование ошибок HTTP
- Особая обработка для кодов 403 (блокировка)
- Детальное логирование исключений

## Поток данных в системе

1. **Сбор данных**: Пауки обходят сайты и извлекают необработанные данные
2. **Валидация**: ValidationPipeline проверяет и нормализует данные
3. **Экспорт**: Экспортеры сохраняют обработанные данные в нужном формате

## Руководство по добавлению нового парсера

Если возникнет необходимость добавить парсер для нового сайта, следуйте этим шагам:

### 1. Создание файла паука

Создайте новый файл в директории `competitors_parser/spiders/`, например `newsite.py`:

```python
from typing import Any, Dict, Iterator

from scrapy import Request
from scrapy.http import Response

from .base import BaseCompetitorSpider


class NewSiteSpider(BaseCompetitorSpider):
    """Паук для парсинга сайта newsite.com."""
    name = "newsite"
    allowed_domains = ["newsite.com"]
    start_urls = ["https://newsite.com/catalog/"]

    def parse(self, response: Response) -> Iterator[Request]:
        """Парсинг главной страницы каталога."""
        # Извлечение категорий
        categories = response.css('ваш_селектор_категорий')
        
        for category in categories:
            category_name = category.css('селектор_имени::text').get('')
            category_url = category.css('селектор_ссылки::attr(href)').get()
            
            if category_url:
                self.logger.info(f'Category: {category_name} - {category_url}')
                
                yield Request(
                    url=response.urljoin(category_url),
                    callback=self.parse_category,
                    cb_kwargs={'category': category_name}
                )

    def parse_category(self, response: Response, category: str) -> Iterator[Request]:
        """Парсинг страницы категории."""
        # Извлечение ссылок на товары
        products = response.css('ваш_селектор_продуктов')
        
        for product in products:
            product_url = product.css('селектор_ссылки::attr(href)').get()
            
            if product_url:
                yield Request(
                    url=response.urljoin(product_url),
                    callback=self.parse_product,
                    cb_kwargs={'category': category}
                )
        
        # Обработка пагинации если есть
        next_page = response.css('селектор_следующей_страницы::attr(href)').get()
        if next_page:
            yield Request(
                url=response.urljoin(next_page),
                callback=self.parse_category,
                cb_kwargs={'category': category}
            )

    def parse_product(self, response: Response, category: str) -> Iterator[Dict[str, Any]]:
        """Парсинг страницы товара."""
        try:
            # Извлечение данных товара
            name = response.css('селектор_имени::text').get('')
            name = self.clean_text(name)
            
            price_text = response.css('селектор_цены::text').get('')
            price = self.extract_price(price_text)
            
            # Создание стандартизированного элемента данных
            yield {
                'category': category,
                'product_code': response.css('селектор_кода::text').get(''),
                'name': name,
                'price': price,
                'stocks': [{
                    'stock': 'Основной',
                    'quantity': 0,  # Заполните данные о количестве если доступны
                    'price': price
                }],
                'unit': response.css('селектор_единицы::text').get('') or 'шт',
                'currency': 'RUB',
                'url': response.url
            }
            
        except Exception as e:
            self.logger.error(f"Error parsing product {response.url}: {str(e)}")
```

### 2. Выбор подхода к парсингу

В зависимости от особенностей сайта, выберите один из подходов:

#### Статические страницы (HTML)

Если сайт состоит из статических HTML-страниц, используйте подход похожий на `RemexSpider` или `ZenonSpider`.

#### Сайты с API

Если сайт использует API для загрузки данных, см. пример в `OracalSpider` или `FordaSpider`.

#### Динамический контент (JavaScript)

Если сайт загружает данные динамически с использованием JavaScript, используйте подход с Playwright как в `TdpplSpider`.

### 3. Использование специальных экспортеров

Если ваш паук использует Playwright, добавьте соответствующие настройки в `custom_settings`:

```python
custom_settings = {
    'ITEM_PIPELINES': {
        'competitors_parser.pipelines.validation.ValidationPipeline': 300,
        'competitors_parser.exporters.playwright_csv_exporter.PlaywrightCSVExporter': 400,
        'competitors_parser.exporters.playwright_json_exporter.PlaywrightJSONExporter': 500,
    }
}
```

### 4. Тестирование паука

Запустите паук с помощью команды:

```bash
scrapy crawl newsite
```

Для отладки используйте режим ограниченного количества страниц:

```bash
scrapy crawl newsite -s CLOSESPIDER_PAGECOUNT=10
```

### 5. Оптимизация паука

При необходимости, настройте специфические параметры в `custom_settings`:

```python
custom_settings = {
    "DOWNLOAD_TIMEOUT": 30,
    "DOWNLOAD_DELAY": 2,
    "CONCURRENT_REQUESTS": 8,
}
```

## Особенности обработки разных типов данных

### Цены

Для извлечения цен используйте метод `extract_price` базового паука, который учитывает различные форматы цен и обрабатывает специальные случаи (цена по запросу).

### Склады

Информация о складах должна быть представлена в виде списка словарей:

```python
[
    {
        'stock': 'Название склада',
        'quantity': 10,  # количество на складе
        'price': 100.0  # цена на данном складе
    }
]
```

### Единицы измерения

Единицы измерения могут быть представлены строкой или списком строк:

```python
unit = 'шт'  # строка
# или
unit = ['За пог.м', 'За кг']  # список
```

## Заключение

Проект предоставляет гибкую архитектуру для парсинга данных с различных сайтов конкурентов. Модульная структура позволяет легко добавлять новые источники данных и расширять функциональность.

При добавлении новых парсеров рекомендуется придерживаться существующей архитектуры и стандартов форматирования данных, чтобы обеспечить единообразие и совместимость.
