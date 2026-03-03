from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

RPA_PATH = BASE_DIR / "RPA" / "RpaBank_report.txt"
PINDODO_PATH = BASE_DIR / "PINDODO" / "Pindodo_report.txt"
OUTPUT_PATH = BASE_DIR / "Результат" / "reconciliation.xlsx"

# Ключи сверки
RPA_MERGE_KEYS = ["date", "amount", "currency", "card_number", "terminal_id"]
PINDODO_MERGE_KEYS = [
    "transaction_date",
    "amount",
    "currency",
    "card_number",
    "terminal_id",
]
