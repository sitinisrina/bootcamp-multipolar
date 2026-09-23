import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime, date as DateType
from beanie import Document, init_beanie, PydanticObjectId
from pymongo import AsyncMongoClient
from enum import Enum

load_dotenv()

MONGO_USER = os.environ["MONGO_USER"]
MONGO_PASSWORD = os.environ["MONGO_PASSWORD"]
MONGO_HOST = os.environ["MONGO_HOST"]
MONGO_URI = f"mongodb+srv://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}/?appName=Cluster1"
MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME", "bootcamp")

app = FastAPI()


class PaymentMethod(str, Enum):
    BCA = "bca"
    BNI = "bni"
    BRI = "bri"
    MANDIRI = "mandiri"
    GOPAY = "gopay"
    OVO = "ovo"
    SHOPEEPAY = "shopeepay"
    DANA = "dana"
    CASH = "cash"


class TrxType(str, Enum):
    INCOME = "income"
    OUTCOME = "outcome"


class Transaction(Document):
    date: datetime
    amount: int = Field(gt=0)
    method: PaymentMethod
    desc: str
    trx_type: TrxType

    class Settings:
        name = "trx_collection"


class RequestNewTransaction(BaseModel):
    amount: int = Field(gt=0)
    method: PaymentMethod
    desc: str
    trx_type: TrxType
    date: DateType | None = None

    @field_validator("date")
    @classmethod
    def date_not_in_future(cls, v):
        if v is not None and v > datetime.now().date():
            raise ValueError("Tanggal tidak boleh di masa depan")
        return v


class RequestEditTransaction(BaseModel):
    amount: int | None = Field(default=None, gt=0)
    method: PaymentMethod | None = None
    desc: str | None = None
    trx_type: TrxType | None = None
    date: DateType | None = None

    @field_validator("date")
    @classmethod
    def date_not_in_future(cls, v):
        if v is not None and v > datetime.now().date():
            raise ValueError("Tanggal tidak boleh di masa depan")
        return v


from category import classify_spending

@app.on_event("startup")
async def init_db():
    client = AsyncMongoClient(MONGO_URI)
    await init_beanie(database=client[MONGO_DB_NAME], document_models=[Transaction])


@app.post("/transaction/add")
async def add_transaction(request_body: RequestNewTransaction):
    if request_body.date is not None:
        trx_date = datetime.combine(request_body.date, datetime.min.time())
    else:
        trx_date = datetime.combine(datetime.now().date(), datetime.min.time())

    trx = Transaction(
        date=trx_date,
        amount=request_body.amount,
        method=request_body.method,
        desc=request_body.desc,
        trx_type=request_body.trx_type,
    )
    await trx.insert()
    return trx


@app.get("/transaction")
async def get_transaction(start_date: datetime, end_date: datetime):
    return await Transaction.find(
        Transaction.date >= start_date, Transaction.date <= end_date
    ).to_list()


@app.get("/transaction/summary")
async def summary_by_method(year: int, month: int):
    start = datetime(year, month, 1)
    if month == 12:
        end = datetime(year + 1, 1, 1)
    else:
        end = datetime(year, month + 1, 1)

    pipeline = [
        {"$match": {"date": {"$gte": start, "$lt": end}}},
        {"$group": {"_id": "$trx_type", "total_amount": {"$sum": "$amount"}, "count": {"$sum": 1}}},
    ]

    results = await Transaction.aggregate(pipeline).to_list()

    totals = {"income": 0, "outcome": 0}
    for r in results:
        totals[r["_id"]] = r["total_amount"]

    category_result = classify_spending(totals["income"], totals["outcome"])

    return {
        "summary": results,
        "ratio": category_result["ratio"],
        "category": category_result["category"],
    }

@app.delete("/transaction/{trx_id}")
async def delete_transaction(trx_id: PydanticObjectId):
    trx = await Transaction.get(trx_id)
    if trx is None:
        raise HTTPException(status_code=404, detail="Transaction not found")

    await trx.delete()
    return {"message": "Transaction deleted", "id": str(trx_id)}


@app.patch("/transaction/{trx_id}")
async def edit_transaction(trx_id: PydanticObjectId, request_body: RequestEditTransaction):
    trx = await Transaction.get(trx_id)
    if trx is None:
        raise HTTPException(status_code=404, detail="Transaction not found")

    update_data = request_body.model_dump(exclude_unset=True)

    if "date" in update_data:
        update_data["date"] = datetime.combine(update_data["date"], datetime.min.time())

    for field, value in update_data.items():
        setattr(trx, field, value)

    await trx.save()
    return trx
