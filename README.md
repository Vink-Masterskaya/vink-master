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

4. Создайте необходимые директории:
```bash
mkdir -p data/exports/zenon
mkdir -p data/exports/remex
mkdir -p logs
```

5. Скопируйте файл с настройками:
```bash
cp .env.example .env
```

### Структура проекта

```
competitors_parser/
├── competitors_parser/     # Основной код
├── data/                  # Данные
│   └── exports/          # Результаты парсинга
├── logs/                 # Логи
├── scripts/              # Скрипты управления
├── tests/                # Тесты
├── requirements.txt      # Зависимости
├── README.md            
├── .env.example         # Пример настроек
└── scrapy.cfg           # Конфигурация Scrapy
```

### Запуск парсера

```bash
# Запуск парсера Zenon
python scripts/run_spider.py zenon

# Запуск парсера Remex
python scripts/run_spider.py remex
```
