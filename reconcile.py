import pandas as pd
from config import PINDODO_MERGE_KEYS, RPA_MERGE_KEYS
from loguru import logger


def reconcile(
    df_rpa: pd.DataFrame,
    df_pin: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    logger.info(f"Начинаем сверку: RpaBank={len(df_rpa)}, Pindodo={len(df_pin)}")

    merged = df_rpa.merge(
        df_pin,
        left_on=RPA_MERGE_KEYS,
        right_on=PINDODO_MERGE_KEYS,
        how="outer",
        suffixes=("_rpa", "_pin"),
        indicator=True,
    )

    success = (
        merged[merged["_merge"] == "both"].drop(columns="_merge").reset_index(drop=True)
    )
    rpa_only = (
        merged[merged["_merge"] == "left_only"]
        .drop(columns="_merge")
        .reset_index(drop=True)
    )
    pind_only = (
        merged[merged["_merge"] == "right_only"]
        .drop(columns="_merge")
        .reset_index(drop=True)
    )

    total = len(success) + len(rpa_only) + len(pind_only)
    match_pct = len(success) / total * 100 if total else 0

    logger.info(f"✓ Успешные:         {len(success)} ({match_pct:.1f}%)")
    logger.info(f"✗ Только RpaBank:   {len(rpa_only)}")
    logger.info(f"✗ Только Pindodo:   {len(pind_only)}")

    if len(rpa_only):
        logger.debug(f"RpaBank-неуспешные RRN: {rpa_only['card_number'].tolist()}")
    if len(pind_only):
        logger.debug(f"Pindodo-неуспешные RRN: {pind_only['card_number'].tolist()}")

    return success, rpa_only, pind_only
