# Honda CRX Shell Tracker – System Specification

## Goal
Continuously monitor U.S. listings for 1987 Honda CRX Si (primary) and 1986 Honda CRX Si (secondary, penalized) to identify clean shells suitable for an AWD electric conversion.

Priorities:
- Clean, rust-free body
- Intact exterior trim
- Good interior (crack-free dash strongly preferred)
- Engine condition not a priority

Outputs:
- Ranked Excel report
- Private web dashboard
- Historical tracking (ACTIVE / SOLD / REMOVED)

## Deployment
- Hardware: Raspberry Pi 5
- OS: Raspberry Pi OS (Server/Lite)
- Runtime: Python 3.11+
- DB: SQLite
- Web Port: 1987
- Access: LAN + port-forwarded WAN
- Auth: Passcode (hashed)

## Execution
- Scraper runs every 30 minutes (cron)
- Idempotent, restart-safe

## Data Sources
Primary Aggregators:
- SearchTempest (FB Marketplace, Craigslist, partial eBay)
- AutoTempest (Craigslist, eBay, Cars.com, Autotrader)

Classic/Collector:
- ClassicCars.com
- Hemmings
- Classic.com
- Classics on Autotrader

Auctions (occasional):
- eBay Motors
- Bring a Trailer
- Mecum Auctions

## Storage
SQLite tables:
- listings (lifecycle + scoring)
- price_history (per-listing price changes)
- sales (verified sales only)

Listings retain URLs forever, including SOLD/REMOVED.

## Location & Distance
- Home ZIP: 37411
- Driving distance via free OSM routing (OSRM/OpenRouteService)
- Cached by city/state

## Model Years
- 1987: preferred
- 1986: allowed, −25 applied post-score

## Scoring
- Start at 0
- Positives add points
- Only deductions:
  - Distance
  - Year (1986)

Positives (examples):
- Rust free / no rust
- Clean/straight body
- All/OEM trim
- Crack-free dash
- Clean/good interior
- Clean title

## Distance Deduction
0–200: 0
201–500: −2
501–1000: −5
1001–1500: −8
1500+: −10

## Final Score
Final = positives − distance_deduction − year_deduction

## Mileage
- Tracked (chassis mileage)
- Never affects score
- Mileage Band (derived): Low / Medium / High / Very High / Unknown
- Odometer Notes preserved

## Sales
- Record ONLY when true sale price is known
- Store: source, model_year, sale_price, sale_year, sold_at
- Reject if price unavailable

## Excel Output
Columns include:
- Final Score
- Positives Found
- Distance Deduction
- Year Deduction
- Estimated Driving Miles
- Status
- Price
- Mileage
- Mileage Band
- Odometer Notes
- City/State
- Source
- URL
- First/Last Seen
- Raw Description

## Web Dashboard
- Flask, read-only
- Auth required
- Sorting + search (server-side)
- Detail view per listing
- Port 1987

## Security
- Nginx reverse proxy
- Fail2Ban
- No anonymous access

