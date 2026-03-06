from scrapers.ebay_scraper import scrape_ebay


def main():

    results = scrape_ebay()

    print("\n============================")
    print(f"TOTAL LISTINGS: {len(results)}")
    print("============================\n")

    for i, listing in enumerate(results, 1):
        print(f"{i}. [{listing['source'].upper()}]")
        print(f"   Title: {listing['title']}")
        print(f"   Price: {listing['price']}")
        print(f"   Location: {listing['location']}")
        print(f"   Link: {listing['link']}")
        print("-" * 60)


if __name__ == "__main__":
    main()
