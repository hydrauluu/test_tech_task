from config import OUTPUT_PATH, PINDODO_PATH, RPA_PATH
from export import export_to_excel
from parsers import parse_pindodo, parse_rpabank
from reconcile import reconcile

df_rpa = parse_rpabank(RPA_PATH)
df_pin = parse_pindodo(PINDODO_PATH)

success, rpa_only, pind_only = reconcile(df_rpa, df_pin)


export_to_excel(success, rpa_only, pind_only, OUTPUT_PATH)
