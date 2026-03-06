import sqlite3
import requests
import re
from bs4 import BeautifulSoup

DB_PATH = "/opt/car-search/data/car_search.db"

ALLOWED_MAKES = ["toyota", "honda", "nissan"]
MIN_YEAR = 2023
MAX_MILEAGE = 40000

SUV_TERMS = [
    "suv",
    "sport utility",
    "crossover"
]

USED_TERMS = [
    "used",
    "pre-owned",
    "preowned",
    "certified",
    "cpo"
]


def get_scrapable_dealers():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT place_id, name, inventory_url
        FROM dealers
        WHERE scrape_status = 'scrapable'
        AND inventory_url IS NOT NULL
    """)

    dealers = cur.fetchall()
    conn.close()

    return dealers


def vehicle_qualifies(vehicle):
    make = (vehicle.get("make") or "").lower()
    year = vehicle.get("year")
    mileage = vehicle.get("mileage")
    body = vehicle.get("body","").lower()
    condition = vehicle.get("condition","").lower()

    if make not in ALLOWED_MAKES:
        return False

    if not year or int(year) < MIN_YEAR:
        return False

    if mileage and int(mileage) > MAX_MILEAGE:
        return False

    if not any(term in body for term in SUV_TERMS):
        return False

    if not any(term in condition for term in USED_TERMS):
        return False

    return True


def insert_vehicle(vehicle):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT OR IGNORE INTO listings (
                dealer_place_id,
                vin,
                stock_number,
                make,
                model,
                year,
                price,
                mileage,
                body_type,
                transmission,
                drivetrain,
                fuel_type,
                title_status,
                listing_url,
                image_url
            )
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            vehicle.get("dealer_place_id"),
            vehicle.get("vin"),
            vehicle.get("stock"),
            vehicle.get("make"),
            vehicle.get("model"),
            vehicle.get("year"),
            vehicle.get("price"),
            vehicle.get("mileage"),
            vehicle.get("body"),
            vehicle.get("transmission"),
            vehicle.get("drivetrain"),
            vehicle.get("fuel"),
            vehicle.get("title"),
            vehicle.get("url"),
            vehicle.get("image")
        ))

        conn.commit()

    except Exception as e:
        print("DB insert error:", e)

    conn.close()


def scrape_inventory(dealer):

    url = dealer["inventory_url"]

    print("\nDealer:", dealer["name"])
    print("Inventory:", url)

    try:
        resp = requests.get(url, timeout=15, headers={"User-Agent":"Mozilla/5.0"})
        html = resp.text
    except Exception as e:
        print("Inventory fetch failed:", e)
        return

    soup = BeautifulSoup(html, "html.parser")

    vehicles = soup.find_all("div")

    for v in vehicles:

        text = v.get_text(" ", strip=True)

        year_match = re.search(r"(20\d{2})", text)
        mileage_match = re.search(r"([\d,]+)\s*miles", text.lower())
        price_match = re.search(r"\$([\d,]+)", text)

        year = int(year_match.group(1)) if year_match else None
        mileage = int(mileage_match.group(1).replace(",","")) if mileage_match else None
        price = int(price_match.group(1).replace(",","")) if price_match else None

        make = None
        model = None

        for m in ALLOWED_MAKES:
            if m in text.lower():
                make = m
                break

        vehicle = {
            "dealer_place_id": dealer["place_id"],
            "vin": None,
            "stock": None,
            "make": make,
            "model": model,
            "year": year,
            "price": price,
            "mileage": mileage,
            "body": text,
            "condition": text,
            "transmission": None,
            "drivetrain": None,
            "fuel": None,
            "title": None,
            "url": url,
            "image": None
        }

        if vehicle_qualifies(vehicle):

            print("Qualified vehicle:", year, make, price, mileage)

            insert_vehicle(vehicle)


def run_vehicle_scraper():

    dealers = get_scrapable_dealers()

    for dealer in dealers:
        scrape_inventory(dealer)


if __name__ == "__main__":
    run_vehicle_scraper()
