import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pymongo import AsyncMongoClient

load_dotenv()

from profiling import profiling_summary

MONGO_URI = os.environ["MONGO_URI"]
MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME", "bootcamp")
MONGO_COLLECTION = os.environ.get("MONGO_COLLECTION", "trx_collection")

app = FastAPI()
collection = AsyncMongoClient(MONGO_URI)[MONGO_DB_NAME][MONGO_COLLECTION]


@app.get("/profiling/summary")
async def get_profiling_summary(year: int, month: int):
    if not 1 <= month <= 12:
        raise HTTPException(status_code=400, detail="Bulan harus antara 1 sampai 12")
    return await profiling_summary(collection, year, month)