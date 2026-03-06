from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time

SEARCH_TERMS = [
    "1987 Honda CRX Si",
    "1987 Honda CRX",
    "1986 Honda CRX Si",
    "1986 Honda CRX"
]

BASE_URL = "https://www.ebay.com/sch/i.html?_sacat=6001_sacat=6001&_nkw=LH_ItemCondition=3000_sacat=6001&_nkw=_nkw="

def create_driver():
    options = Options()
    options.binary_location = "/usr/bin/chromium"
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1920,1080")

    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def scrape_ebay():
    driver = create_driver()
    all_results = []

    for term in SEARCH_TERMS:
        url = BASE_URL + term.replace(" ", "+")
        driver.get(url)

        time.sleep(5)

        items = driver.find_elements(By.CSS_SELECTOR, ".s-card")
        print("Items found:", len(items))

        for item in items:
            try:
                title = item.find_element(By.CSS_SELECTOR, ".s-card__title").text
            except:
                continue

            if "Shop on eBay" in title:
                continue

            try:
                price = item.find_element(By.CSS_SELECTOR, ".s-card__price").text
            except:
                price = None

            try:
                location = item.find_element(By.CSS_SELECTOR, ".s-card__location").text
            except:
                location = None

            try:
                link = item.find_element(By.CSS_SELECTOR, "a.s-card__link").get_attribute("href")
            except:
                link = None

            listing = {
                "source": "ebay",
                "title": title,
                "price": price,
                "location": location,
                "link": link
            }

            all_results.append(listing)

    driver.quit()
    return all_results
