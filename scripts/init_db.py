import sqlite3
from pathlib import Path

db_path = Path("data/crx_tracker.db")
db_path.parent.mkdir(parents=True, exist_ok=True)

conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.executescript("""
CREATE TABLE IF NOT EXISTS listings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_hash TEXT UNIQUE NOT NULL,
    source TEXT NOT NULL,
    title TEXT,
    year INTEGER,
    price INTEGER,
    mileage INTEGER,
    city TEXT,
    state TEXT,
    estimated_driving_miles INTEGER,
    positives_found TEXT,
    final_score INTEGER,
    distance_deduction INTEGER,
    year_deduction INTEGER,
    status TEXT CHECK(status IN ('ACTIVE','SOLD','REMOVED')) NOT NULL,
    listing_url TEXT NOT NULL,
    raw_description TEXT,
    first_seen DATETIME NOT NULL,
    last_seen DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS price_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_hash TEXT NOT NULL,
    price INTEGER,
    seen_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_hash TEXT UNIQUE NOT NULL,
    source TEXT NOT NULL,
    model_year INTEGER NOT NULL,
    sale_price INTEGER NOT NULL,
    sale_year INTEGER NOT NULL,
    sold_at DATETIME NOT NULL
);
""")

conn.commit()
conn.close()

print("Database initialized at data/crx_tracker.db")
