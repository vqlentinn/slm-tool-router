"""Fixed world. Tasks may only refer to entities defined here."""

WORLD: dict = {
    "policies": {
        "refund_window_days": 14,
        "max_auto_refund_eur": 100,
    },
    "customers": {
        "ada": {"email": "ada@example.com"},
        "grace": {"email": "grace@example.com"},
        "noor": {"email": "noor@example.com"},
        "sam": {"email": "sam@example.com"},
        "lin": {"email": "lin@example.com"},
        "rai": {"email": "rai@example.com"},
    },
    "orders": {
        "A100": {"customer": "ada", "status": "delivered", "total_eur": 40, "delivered_days_ago": 3},
        "B200": {"customer": "ada", "status": "shipped", "total_eur": 120, "delivered_days_ago": None},
        "C300": {"customer": "grace", "status": "delivered", "total_eur": 80, "delivered_days_ago": 30},
        "E500": {"customer": "ada", "status": "delivered", "total_eur": 180, "delivered_days_ago": 2},
        "F600": {"customer": "noor", "status": "delivered", "total_eur": 25, "delivered_days_ago": 1},
        "G700": {"customer": "noor", "status": "shipped", "total_eur": 50, "delivered_days_ago": None},
        "H800": {"customer": "sam", "status": "delivered", "total_eur": 60, "delivered_days_ago": 10},
        "I900": {"customer": "sam", "status": "delivered", "total_eur": 90, "delivered_days_ago": 20},
        "J110": {"customer": "noor", "status": "delivered", "total_eur": 55, "delivered_days_ago": 14},
        "K120": {"customer": "grace", "status": "shipped", "total_eur": 30, "delivered_days_ago": None},
        "D400": {"customer": "lin", "status": "delivered", "total_eur": 15, "delivered_days_ago": 2},
        "L130": {"customer": "rai", "status": "delivered", "total_eur": 45, "delivered_days_ago": 4},
        "M140": {"customer": "rai", "status": "delivered", "total_eur": 70, "delivered_days_ago": 40},
        "N150": {"customer": "lin", "status": "shipped", "total_eur": 22, "delivered_days_ago": None},
    },
}
