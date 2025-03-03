# vink-master
# Парсер данных конкурентов

Система парсинга данных о товарах с сайтов конкурентов (zenonline.ru, remex.ru).

## Локальное развертывание

### Требования
- Python 3.10+
- pip
- venv

### Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/Vink-Masterskaya/vink-master.git
```

2. Создайте виртуальное окружение:
```bash
python -m venv venv

# Linux/macOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

### Структура проекта

```
competitors_parser/
├── competitors_parser/     # Основной код
├── data/                  # Данные
│   └── exports/          # Результаты парсинга
├── logs/                 # Логи
├── requirements.txt      # Зависимости
├── README.md            
└── scrapy.cfg           # Конфигурация Scrapy
```

### Запуск парсера

```bash
# Запуск парсера Fabreex
scrapy crawl fabreex

# Запуск парсера Remex
scrapy crawl remex

# Запуск парсера Forda
scrapy crawl forda

# Запуск парсера Tdppl
scrapy crawl tdppl

# Запуск парсера Zenon
scrapy crawl zenon

# Запуск парсера Oracal
scrapy crawl oracal
```
