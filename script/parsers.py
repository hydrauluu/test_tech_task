import re
from pathlib import Path

import pandas as pd
from loguru import logger

_RPA_RE = re.compile(
    r"^\s*(\d+)\s+(\d+)\s+"
    r"(\d{8})id\S+\s+"
    r"([\d.,]+)([A-Z]{3})"
    r"(\d{6})\s+(\S+)"
)

_PINDODO_FIELDS = {
    "Local Transaction Date and Time": "local_datetime",
    "Transaction Date": "transaction_date",
    "Transaction Amount": "amount",
    "Transaction Currency": "currency",
    "Retrieval Reference Number": "card_number",
    "Card Acceptor Terminal ID": "terminal_id",
}

_PINDODO_RE = re.compile(r"^\s{2,}([A-Za-z][\w\s]+?)\s{2,}(\S.*?)\s*$")


def parse_rpabank(path: str | Path) -> pd.DataFrame:
    logger.info(f"Парсим RpaBank: {path}")
    rows = []

    with open(path, encoding="utf-8") as f:
        for line in f:
            m = _RPA_RE.match(line)
            if m:
                rows.append(m.groups())
            else:
                logger.debug(f"Строка не распознана: {line.rstrip()}")

    if not rows:
        logger.error("RpaBank: не найдено ни одной записи")
        raise ValueError(f"Файл пустой или формат не распознан: {path}")

    df = pd.DataFrame(
        rows,
        columns=[
            "number",
            "index",
            "date",
            "amount",
            "currency",
            "card_number",
            "terminal_id",
        ],
    )
    df["date"] = pd.to_datetime(df["date"], format="%Y%m%d").dt.date
    df["amount"] = df["amount"].str.replace(",", ".").astype(float)
    df["card_number"] = df["card_number"].str.zfill(6)

    logger.info(f"RpaBank: загружено {len(df)} записей")
    logger.debug(f"RpaBank: валюты — {df['currency'].value_counts().to_dict()}")
    return df


def parse_pindodo(path: str | Path) -> pd.DataFrame:
    logger.info(f"Парсим Pindodo: {path}")
    rows, current = [], {}
    columns = list(_PINDODO_FIELDS.values())
    skipped = 0

    def flush(d: dict):
        nonlocal skipped
        if set(columns).issubset(d):
            rows.append([d[c] for c in columns])
        elif d:
            skipped += 1
            logger.debug(
                f"Pindodo: блок пропущен, не хватает полей: {set(columns) - set(d)}"
            )

    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\r\n")
            if re.match(r"^\s*-{10,}\s*$", line):
                flush(current)
                current = {}
                continue
            m = _PINDODO_RE.match(line)
            if m:
                key = m.group(1).strip()
                if key in _PINDODO_FIELDS:
                    current[_PINDODO_FIELDS[key]] = m.group(2).strip()

    flush(current)

    if not rows:
        logger.error("Pindodo: не найдено ни одной записи")
        raise ValueError(f"Файл пустой или формат не распознан: {path}")

    if skipped:
        logger.warning(f"Pindodo: пропущено {skipped} неполных блоков")

    df = pd.DataFrame(rows, columns=columns)
    df["local_datetime"] = pd.to_datetime(df["local_datetime"], format="%Y%m%d%H%M%S")
    df["transaction_date"] = pd.to_datetime(
        df["transaction_date"], format="%Y-%m-%d"
    ).dt.date
    df["amount"] = df["amount"].str.replace(",", ".").astype(float)
    df["card_number"] = df["card_number"].str.zfill(6)

    logger.info(f"Pindodo: загружено {len(df)} записей")
    logger.debug(f"Pindodo: валюты — {df['currency'].value_counts().to_dict()}")
    return df
