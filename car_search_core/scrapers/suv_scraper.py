from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


def search_suvs(make_list, min_year, max_miles, zip_code, radius):

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)

    results = []

    for make in make_list:
        url = (
            f"https://www.cars.com/shopping/results/?"
            f"dealer_id=&keyword=&list_price_max=&list_price_min=&"
            f"makes[]={make}&maximum_distance={radius}&"
            f"mileage_max={max_miles}&page_size=20&"
            f"sort=best_match_desc&stock_type=used&"
            f"year_min={min_year}&zip={zip_code}"
        )

        driver.get(url)

        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "vehicle-card"))
            )
        except:
            continue

        cards = driver.find_elements(By.CLASS_NAME, "vehicle-card")

        for card in cards:
            try:
                title = card.find_element(By.CLASS_NAME, "title").text
                price = card.find_element(By.CLASS_NAME, "primary-price").text
                mileage = card.find_element(By.CLASS_NAME, "mileage").text
                link = card.find_element(By.TAG_NAME, "a").get_attribute("href")

                image = None
                try:
                    image = card.find_element(By.TAG_NAME, "img").get_attribute("src")
                except:
                    pass

                results.append({
                    "title": title,
                    "price": price,
                    "mileage": mileage,
                    "link": link,
                    "image": image,
                    "make": make
                })

            except:
                continue

    driver.quit()
    return results
