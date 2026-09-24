RECKLESS_THRESHOLD = 0.75

def classify_spending(total_income: int, total_outcome: int) -> dict:
    """
    Kategorisasi berdasarkan rasio outcome/income.
    Opsi A: kalau income = 0 (baik outcome juga 0, atau outcome > 0),
    nggak ada basis pembagi yang valid -> category = None.
    """
    if total_income == 0:
        return {"ratio": None, "category": None}

    ratio = total_outcome / total_income
    category = "reckless_spender" if ratio > RECKLESS_THRESHOLD else "big_saver"

    return {"ratio": round(ratio, 4), "category": category}