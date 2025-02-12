
## REMEX

Основные элементы:
1. Каталог: https://www.remex.ru/catalog
   - Категории: .catalog-category
   - Подкатегории: .subcategory-item

2. Страница категории:
   - Товары: .product-item
   - Пагинация: .pagination

3. Карточка товара:
   - Артикул: .product-code
   - Название: .product-name
   - Цена: .price
   - Количество: .stock
   - Единица измерения: .unit

scrapy crawl remex -O remex.json

