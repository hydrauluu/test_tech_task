from config import OUTPUT_PATH, PINDODO_PATH, RPA_PATH
from export import export_to_excel
from logger import setup_logger
from loguru import logger
from parsers import parse_pindodo, parse_rpabank
from reconcile import reconcile

if __name__ == "__main__":
    setup_logger()
    logger.info("=== Запуск сверки ===")

    try:
        df_rpa = parse_rpabank(RPA_PATH)
        df_pin = parse_pindodo(PINDODO_PATH)

        success, rpa_only, pind_only = reconcile(df_rpa, df_pin)

        export_to_excel(success, rpa_only, pind_only, OUTPUT_PATH)

        logger.info("=== Сверка завершена успешно ===")

    except FileNotFoundError as e:
        logger.error(f"Файл не найден: {e}")
        raise
    except Exception as e:
        logger.exception(f"Неожиданная ошибка: {e}")
        raise
