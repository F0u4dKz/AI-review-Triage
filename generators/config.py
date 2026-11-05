from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SEED = 42
FAKER_LOCALE = "fr_FR"

N_CLIENTS = 50
N_ORDERS = 100
ORDER_WINDOW_DAYS = 90

LATE_DELIVERY_RATE = 0.2

TRANSACTIONS_DIR = ROOT / "landing" / "transactions"
GROUND_TRUTH_PATH = ROOT / "data" / "mock" / "reviews_ground_truth.jsonl"

API_URL = "http://localhost:8000/webhook/reviews"
API_KEY = "dev-key"
STREAM_INTERVAL_SECONDS = 2.0

MISMATCH_RATE = 0.10
PII_RATE = 0.10
DUPLICATE_RATE = 0.05

CATEGORIES = ["Electronics", "Home", "Fashion", "Beauty", "Sports"]

PRODUCTS = [
    (1, 1, "Wireless Earbuds", 59.90),
    (2, 1, "Smart Watch", 129.00),
    (3, 2, "Coffee Maker", 89.50),
    (4, 2, "Desk Lamp", 34.90),
    (5, 3, "Denim Jacket", 74.00),
    (6, 3, "Running Cap", 19.90),
    (7, 4, "Face Serum", 29.90),
    (8, 4, "Hair Dryer", 49.00),
    (9, 5, "Yoga Mat", 24.90),
    (10, 5, "Dumbbell Set", 69.00),
]

CARRIERS = ["Colissimo", "Chronopost", "DHL", "UPS"]
PAYMENT_METHODS = ["card", "paypal", "bank_transfer"]
REVIEW_SOURCES = ["form", "shopify", "zendesk"]
