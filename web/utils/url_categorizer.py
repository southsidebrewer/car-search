# url_categorizer.py
# Purpose: Detect dealer inventory URLs and categorize dealer websites as scrapable, unwanted, or research

import sqlite3
import requests
import re

DB_PATH = "/opt/car-search/data/car_search.db"

TARGET_RESULTS = 50
MAX_DEALERS_TO_CHECK = None


def get_dealers_ordered_by_distance(limit=None):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    query = """
        SELECT *
        FROM dealers
        WHERE scrape_status IS NULL
        ORDER BY CAST(REPLACE(drive_distance,' km','') AS REAL) ASC
    """

    if limit:
        query += f" LIMIT {limit}"

    cur.execute(query)
    dealers = cur.fetchall()
    conn.close()

    return dealers


def detect_inventory_url(base_url):
    if not base_url:
        print("No website URL provided.")
        return None

    clean_base = base_url.split("?")[0].rstrip("/")

    try:
        resp = requests.get(clean_base, timeout=10, headers={"User-Agent":"Mozilla/5.0"})
        html = resp.text
        print(f"  Homepage status: {resp.status_code}")
    except Exception as e:
        print(f"  Failed to fetch homepage: {e}")
        return None

    patterns = [
        r'href="([^"]*inventory[^"]*)"',
        r'href="([^"]*used[^"]*inventory[^"]*)"',
        r'href="([^"]*vehicles[^"]*)"',
        r'/api/[^"]*inventory[^"]*',
        r'inventorySearch[^"]*'
    ]

    for pattern in patterns:
        matches = re.findall(pattern, html, re.IGNORECASE)
        if matches:
            candidate = matches[0]

            if candidate.startswith("http"):
                url = candidate
            else:
                url = clean_base + candidate

            print(f"  Inventory pattern found: {url}")
            return url

    print("  No inventory patterns detected.")
    return None


def update_scan_result(place_id, inventory_url, status, next_scan=None):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        UPDATE dealers
        SET inventory_url = ?,
            scrape_status = ?,
            next_scan = ?
        WHERE place_id = ?
    """, (inventory_url, status, next_scan, place_id))

    conn.commit()
    conn.close()

def run_url_categorizer():
    dealers = get_dealers_ordered_by_distance(limit=MAX_DEALERS_TO_CHECK)

    for dealer in dealers:
        print(f"\nDealer: {dealer['name']}")
        print(f"Distance: {dealer['drive_distance']}")
        print(f"Website: {dealer['website']}")

        inventory_url = detect_inventory_url(dealer["website"].split("?")[0])

        if inventory_url:
            print(f"Inventory endpoint detected: {inventory_url}")
            update_scan_result(dealer["place_id"], inventory_url, ("unwanted" if "new" in inventory_url.lower() else "scrapable"), None)
        else:
            print("No inventory endpoint detected.")
            update_scan_result(dealer["place_id"], None, "research", None)

if __name__ == "__main__":
    run_url_categorizer()


