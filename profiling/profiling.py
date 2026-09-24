import os
import random
from datetime import datetime

WINDOW_MONTHS = int(os.environ.get("PROFILING_WINDOW_MONTHS", "3"))

OVER_LIMIT_MESSAGES = [
    "Pengeluaranmu bulan ini sudah lewat dari biasanya, tapi gapapa! Bulan depan pasti bisa lebih hemat 💪",
    "Wah, bulan ini agak boros nih. Tetap semangat, kamu pasti bisa atur lagi! 🔥",
    "Pengeluaran sudah di atas rata-rata, pelan-pelan dikurangi ya. Kamu hebat sudah mau mencatat! 🌱",
]

SAFE_MESSAGES = [
    "Mantap! Pengeluaranmu masih di bawah rata-rata, pertahankan ya 👍",
    "Keuanganmu bulan ini masih aman, keep it up! ✨",
]


def shift_month(year: int, month: int, delta: int) -> tuple[int, int]:
    # contoh: shift_month(2026, 1, -3) -> (2025, 10)
    index = year * 12 + (month - 1) + delta
    return index // 12, index % 12 + 1


def month_start(year: int, month: int) -> datetime:
    return datetime(year, month, 1)


async def get_monthly_outcome(collection, start: datetime, end: datetime) -> list[dict]:
    pipeline = [
        {"$match": {"trx_type": "outcome", "date": {"$gte": start, "$lt": end}}},
        {
            "$group": {
                "_id": {"year": {"$year": "$date"}, "month": {"$month": "$date"}},
                "total": {"$sum": "$amount"},
            }
        },
        {"$sort": {"_id.year": 1, "_id.month": 1}},
    ]
    cursor = await collection.aggregate(pipeline)
    results = await cursor.to_list()
    return [
        {"year": r["_id"]["year"], "month": r["_id"]["month"], "total": r["total"]}
        for r in results
    ]


async def profiling_summary(collection, year: int, month: int) -> dict:
    # Window = WINDOW_MONTHS bulan sebelum bulan yang dievaluasi (bulan itu sendiri tidak ikut)
    window_start = month_start(*shift_month(year, month, -WINDOW_MONTHS))
    current_start = month_start(year, month)
    current_end = month_start(*shift_month(year, month, 1))

    window_months = await get_monthly_outcome(collection, window_start, current_start)

    if len(window_months) < WINDOW_MONTHS:
        return {
            "available": False,
            "message": f"Belum bisa menampilkan profiling, butuh data pengeluaran "
                       f"{WINDOW_MONTHS} bulan sebelumnya (baru ada {len(window_months)} bulan)",
            "window_months": window_months,
        }

    moving_avg = sum(m["total"] for m in window_months) / WINDOW_MONTHS

    current = await get_monthly_outcome(collection, current_start, current_end)
    current_total = current[0]["total"] if current else 0

    over_limit = current_total > moving_avg

    return {
        "available": True,
        "year": year,
        "month": month,
        "window_months": window_months,
        "moving_avg": round(moving_avg),
        "current_total": current_total,
        "percentage_of_avg": round(current_total / moving_avg * 100, 1),
        "over_limit": over_limit,
        "message": random.choice(OVER_LIMIT_MESSAGES if over_limit else SAFE_MESSAGES),
    }