import os
import math
import requests
import sqlite3
import re
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

PLACES_NEARBY_URL = "https://places.googleapis.com/v1/places:searchNearby"
DISTANCE_MATRIX_URL = "https://maps.googleapis.com/maps/api/distancematrix/json"
GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"

MAX_PLACES_RADIUS_METERS = 50000  # Google hard limit (50km)

OEM_BRANDS = [
    "acura","audi","bmw","buick","cadillac","chevrolet","chrysler","dodge",
    "ford","gmc","honda","hyundai","infiniti","jeep","kia","lexus","lincoln",
    "mazda","mercedes","mini","mitsubishi","nissan","ram","subaru","tesla",
    "toyota","volkswagen","volvo","porsche","land rover","jaguar","genesis"
]

MOTORCYCLE_KEYWORDS = [
    "motorcycle","powersports","harley","yamaha","kawasaki",
    "suzuki","ducati","triumph","ktm","can-am","polaris"
]


def geocode_zip(zip_code):
    resp = requests.get(
        GEOCODE_URL,
        params={"address": zip_code, "key": API_KEY}
    )
    data = resp.json()

    if data.get("status") != "OK":
        raise ValueError(f"Geocode failed: {data}")

    location = data["results"][0]["geometry"]["location"]
    return location["lat"], location["lng"]


def generate_search_grid(center_lat, center_lng, radius_miles):
    radius_km = radius_miles * 1.60934
    step_km = 60

    points = []

    lat_degree_km = 111
    lng_degree_km = 111 * math.cos(math.radians(center_lat))

    max_offset = int(math.ceil(radius_km / step_km))

    for dx in range(-max_offset, max_offset + 1):
        for dy in range(-max_offset, max_offset + 1):
            offset_km_x = dx * step_km
            offset_km_y = dy * step_km

            distance_from_center = math.sqrt(offset_km_x**2 + offset_km_y**2)
            if distance_from_center <= radius_km:
                lat = center_lat + (offset_km_y / lat_degree_km)
                lng = center_lng + (offset_km_x / lng_degree_km)
                points.append((lat, lng))

    return points


def search_places_at_point(lat, lng):
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,
        "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.location,places.websiteUri"
    }

    body = {
        "includedTypes": ["car_dealer"],
        "maxResultCount": 20,
        "locationRestriction": {
            "circle": {
                "center": {"latitude": lat, "longitude": lng},
                "radius": MAX_PLACES_RADIUS_METERS
            }
        }
    }

    resp = requests.post(PLACES_NEARBY_URL, json=body, headers=headers)
    data = resp.json()

    if "error" in data:
        return []

    return data.get("places", [])


def discover_dealers(zip_code, radius_miles):
    conn = sqlite3.connect("/opt/car-search/data/car_search.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS dealers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        place_id TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        address TEXT,
        website TEXT,
        lat REAL,
        lng REAL,
        drive_distance TEXT,
        drive_time TEXT,
        seed_zip TEXT,
        seed_radius INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    if not API_KEY:
        raise ValueError("Missing GOOGLE_MAPS_API_KEY")

    origin_lat, origin_lng = geocode_zip(zip_code)
    search_points = generate_search_grid(origin_lat, origin_lng, radius_miles)

    unique_dealers = {}

    for lat, lng in search_points:
        places = search_places_at_point(lat, lng)
        for place in places:
            place_id = place.get("id")
            if place_id:
                unique_dealers[place_id] = place

    filtered_places = []

    for place in unique_dealers.values():
        if not place.get("websiteUri","").split("?")[0]:
            continue
        name = place["displayName"]["text"]
        name_lower = name.lower()

        # exclude motorcycles
        if any(keyword in name_lower for keyword in MOTORCYCLE_KEYWORDS):
            continue

        # tokenize into alphabetic words only
        words = re.findall(r"[a-z]+", name_lower)

        # strict OEM match using word tokens
        if not any(brand in words for brand in OEM_BRANDS):
            continue

        filtered_places.append(place)

    dealers = []
    batch_size = 25

    for i in range(0, len(filtered_places), batch_size):
        batch = filtered_places[i:i + batch_size]

        destinations = "|".join(
            f"{p['location']['latitude']},{p['location']['longitude']}"
            for p in batch
        )

        resp = requests.get(
            DISTANCE_MATRIX_URL,
            params={
                "origins": f"{origin_lat},{origin_lng}",
                "destinations": destinations,
                "key": API_KEY
            }
        )

        data = resp.json()
        elements = data.get("rows", [{}])[0].get("elements", [])

        for place, element in zip(batch, elements):
            try:
                drive_distance = element["distance"]["text"]
                drive_time = element["duration"]["text"]
            except Exception:
                drive_distance = None
                drive_time = None

            cursor.execute("""
            INSERT OR IGNORE INTO dealers (
                place_id,name,address,website,lat,lng,drive_distance,drive_time,seed_zip,seed_radius
            ) VALUES (?,?,?,?,?,?,?,?,?,?)
            """, (
                place.get("id"),
                place["displayName"]["text"],
                place.get("formattedAddress"),
                place.get("websiteUri","").split("?")[0],
                place["location"]["latitude"],
                place["location"]["longitude"],
                drive_distance,
                drive_time,
                zip_code,
                radius_miles
            ))

            dealers.append({
                "place_id": place.get("id"),
                "name": place["displayName"]["text"],
                "address": place.get("formattedAddress"),
                "website": place.get("websiteUri","").split("?")[0],
                "lat": place["location"]["latitude"],
                "lng": place["location"]["longitude"],
                "drive_distance": drive_distance,
                "drive_time": drive_time
            })

    conn.commit()
    conn.close()

    return dealers
