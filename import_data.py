import io
import pandas as pd
from main import Transaction, PaymentMethod, TrxType

REQUIRED_COLUMNS = {"datetime", "amount", "payment_method", "description"}

# Mapping value di file sumber -> value enum PaymentMethod yang valid.
# "shopee" di data sumber dipetakan ke "shopeepay" karena itu nama resmi di enum.
METHOD_MAPPING = {
    "shopee": "shopeepay",
}


def parse_amount(raw_amount) -> int:
    # Excel bisa menyimpan amount sebagai angka (misal -243000.0)
    if isinstance(raw_amount, (int, float)):
        return int(raw_amount)
    # contoh input CSV: "-Rp 243,000" atau "Rp 6,248,000"
    cleaned = str(raw_amount).replace("Rp", "").replace(",", "").replace(" ", "").strip()
    return int(cleaned)


def read_file(filename: str, content: bytes) -> pd.DataFrame:
    name = filename.lower()
    if name.endswith(".csv"):
        return pd.read_csv(io.BytesIO(content))
    if name.endswith((".xlsx", ".xls")):
        return pd.read_excel(io.BytesIO(content))
    raise ValueError("Format file harus .csv, .xlsx, atau .xls")


def validate_columns(df: pd.DataFrame):
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Kolom wajib tidak ditemukan: {', '.join(sorted(missing))}")


def row_to_transaction(row) -> Transaction:
    trx_date = pd.to_datetime(row["datetime"]).to_pydatetime()

    signed_amount = parse_amount(row["amount"])
    trx_type = TrxType.OUTCOME if signed_amount < 0 else TrxType.INCOME
    amount = abs(signed_amount)

    raw_method = str(row["payment_method"]).strip().lower()
    method_value = METHOD_MAPPING.get(raw_method, raw_method)

    return Transaction(
        date=trx_date,
        amount=amount,
        method=PaymentMethod(method_value),
        desc=str(row["description"]).strip(),
        trx_type=trx_type,
    )


async def import_dataframe(df: pd.DataFrame) -> dict:
    validate_columns(df)

    transactions = []
    failed_rows = []

    for idx, row in df.iterrows():
        try:
            transactions.append(row_to_transaction(row))
        except Exception as e:
            # +2 = 1 baris header + index mulai dari 0
            failed_rows.append({"row": idx + 2, "error": str(e)})

    if transactions:
        await Transaction.insert_many(transactions)

    return {
        "success_count": len(transactions),
        "failed_count": len(failed_rows),
        "failed_rows": failed_rows,
    }
