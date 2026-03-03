import pandas as pd
from config import PINDODO_MERGE_KEYS, RPA_MERGE_KEYS


def reconcile(
    df_rpa: pd.DataFrame,
    df_pin: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:

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

    return success, rpa_only, pind_only
