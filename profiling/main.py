import os
from urllib.parse import quote_plus

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pymongo import AsyncMongoClient

load_dotenv()

from profiling import profiling_summary

MONGO_USER = quote_plus(os.environ["MONGO_USER"])
MONGO_PASSWORD = quote_plus(os.environ["MONGO_PASSWORD"])
MONGO_HOST = os.environ["MONGO_HOST"]
MONGO_URI = f"mongodb+srv://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}/"
MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME", "bootcamp")
MONGO_COLLECTION = os.environ.get("MONGO_COLLECTION", "trx_collection")

app = FastAPI()
collection = AsyncMongoClient(MONGO_URI)[MONGO_DB_NAME][MONGO_COLLECTION]


@app.get("/profiling/summary")
async def get_profiling_summary(year: int, month: int):
    if not 1 <= month <= 12:
        raise HTTPException(status_code=400, detail="Bulan harus antara 1 sampai 12")
    return await profiling_summary(collection, year, month)