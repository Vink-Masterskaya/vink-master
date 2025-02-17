import pandas as pd
from pathlib import Path
from datetime import datetime
import logging
import sys


def setup_logging():
    """Настройка логирования"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)


def merge_csv_files(input_dir: str, output_file: str = None):
    """
    Объединяет все CSV файлы из указанной директории в один

    Args:
        input_dir (str): Путь к директории с CSV файлами
        output_file (str, optional): Путь к выходному файлу
    """
    logger = setup_logging()

    try:
        # Получаем список всех CSV файлов
        csv_files = list(Path(input_dir).glob('*.csv'))
        if not csv_files:
            logger.error(f"CSV файлы не найдены в директории {input_dir}")
            return

        logger.info(f"Найдено {len(csv_files)} CSV файлов")

        # Читаем все файлы в список DataFrame
        dfs = []
        for file in csv_files:
            try:
                df = pd.read_csv(file, encoding='utf-8')
                df['source_file'] = file.name  # Добавляем имя исходного файла
                dfs.append(df)
                logger.info(f"Прочитан файл: {file.name}")
            except Exception as e:
                logger.error(f"Ошибка при чтении файла {file}: {str(e)}")

        if not dfs:
            logger.error("Не удалось прочитать ни один файл")
            return

        # Объединяем все DataFrame
        result_df = pd.concat(dfs, ignore_index=True)

        # Если выходной файл не указан, создаем имя с текущей датой
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"data/processed/merged_{timestamp}.csv"

        # Сохраняем результат
        result_df.to_csv(output_file, index=False, encoding='utf-8')
        logger.info(f"Результат сохранен в {output_file}")

        # Выводим статистику
        logger.info(f"Всего обработано записей: "
                    f"{len(result_df)}")
        logger.info(f"Уникальных товаров:"
                    f"{result_df['product_code'].nunique()}")

    except Exception as e:
        logger.error(f"Ошибка при объединении файлов: {str(e)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python merge_csv.py <директория_с_csv> [выходной_файл]")
        sys.exit(1)

    input_dir = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    merge_csv_files(input_dir, output_file)
