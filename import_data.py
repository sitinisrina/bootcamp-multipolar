import asyncio
from datetime import datetime
import pandas as pd
from beanie import init_beanie
from pymongo import AsyncMongoClient

from main import Transaction, PaymentMethod, TrxType

CSV_PATH = "data_transaksi.csv"

# Mapping value di file sumber -> value enum PaymentMethod yang valid.
# "shopee" di data sumber dipetakan ke "shopeepay" karena itu nama resmi di enum.
METHOD_MAPPING = {
    "shopee": "shopeepay",
}


def parse_amount(raw_amount: str) -> int:
    # contoh input: "-Rp 243,000" atau "Rp 6,248,000"
    cleaned = raw_amount.replace("Rp", "").replace(",", "").replace(" ", "").strip()
    return int(cleaned)


async def import_data():
    client = AsyncMongoClient("mongodb+srv://stnisrinasalsabila_db_user:3fbB2RLcivUDv666@cluster1.l8xg6o3.mongodb.net/?appName=Cluster1")
    await init_beanie(database=client.bootcamp, document_models=[Transaction])

    df = pd.read_csv(CSV_PATH)

    success_count = 0
    failed_rows = []

    for idx, row in df.iterrows():
        try:
            trx_date = pd.to_datetime(row["datetime"]).to_pydatetime()

            raw_amount = str(row["amount"])
            signed_amount = parse_amount(raw_amount)
            trx_type = TrxType.OUTCOME if signed_amount < 0 else TrxType.INCOME
            amount = abs(signed_amount)

            raw_method = str(row["payment_method"]).strip().lower()
            method_value = METHOD_MAPPING.get(raw_method, raw_method)

            trx = Transaction(
                date=trx_date,
                amount=amount,
                method=PaymentMethod(method_value),
                desc=str(row["description"]).strip(),
                trx_type=trx_type,
            )
            await trx.insert()
            success_count += 1
        except Exception as e:
            failed_rows.append((idx + 2, str(e)))

    print(f"Berhasil import: {success_count} data")
    if failed_rows:
        print(f"Gagal import: {len(failed_rows)} baris")
        for row_num, err in failed_rows:
            print(f"  Baris #{row_num}: {err}")


if __name__ == "__main__":
    asyncio.run(import_data())