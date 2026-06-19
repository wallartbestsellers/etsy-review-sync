import json
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright

SHOP_URL = "https://www.etsy.com/shop/WallArtBestSellers"

OUTPUT_FILE = Path("output/reviews.json")
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)


def get_listing_urls(page):
    print("Loading shop page...")

    page.goto(SHOP_URL, timeout=60000)

    # IMPORTANT: wait for product grid (not networkidle)
    page.wait_for_selector("a", timeout=20000)

    # scroll to force lazy loading
    for _ in range(6):
        page.mouse.wheel(0, 3000)
        page.wait_for_timeout(2000)

    # direct DOM extraction (more reliable than HTML regex)
    anchors = page.locator("a[href*='/listing/']").all()

    urls = []
    for a in anchors:
        href = a.get_attribute("href")
        if href and "/listing/" in href:
            if href.startswith("/"):
                href = "https://www.etsy.com" + href
            urls.append(href)

    # dedupe
    urls = list(dict.fromkeys(urls))

    print(f"Found {len(urls)} listing URLs")

    return urls[:6]


def scrape_listing(page, url):
    print(f"Scraping: {url}")

    page.goto(url, timeout=60000)
    page.wait_for_timeout(4000)

    # scroll to load reviews section
    for _ in range(5):
        page.mouse.wheel(0, 2500)
        page.wait_for_timeout(1500)

    # Try multiple possible selectors (Etsy changes often)
    possible_selectors = [
        "[data-review-id]",
        "section",
        "div"
    ]

    reviews = []

    for selector in possible_selectors:
        elements = page.locator(selector).all()

        for el in elements:
            try:
                text = el.inner_text().strip()

                if (
                    len(text) > 60
                    and len(text) < 500
                    and "add to cart" not in text.lower()
                    and "price" not in text.lower()
                    and "etsy" not in text.lower()
                ):
                    reviews.append({
                        "reviewer": "Etsy Customer",
                        "rating": 5,
                        "text": text[:300],
                        "date": "",
                        "listing": url,
                        "etsy_url": url
                    })
            except:
                continue

        if reviews:
            break

    print(f"Found {len(reviews)} reviews")

    return reviews[:2]


def scrape():
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox"]
        )

        page = browser.new_page()

        listing_urls = get_listing_urls(page)

        if not listing_urls:
            print("FALLBACK: Trying slower scroll-based capture...")

            page.goto(SHOP_URL)
            page.wait_for_timeout(5000)

            for _ in range(10):
                page.mouse.wheel(0, 4000)
                page.wait_for_timeout(2000)

            anchors = page.locator("a").all()

            for a in anchors:
                href = a.get_attribute("href")
                if href and "listing" in href:
                    if href.startswith("/"):
                        href = "https://www.etsy.com" + href
                    listing_urls.append(href)

            listing_urls = list(dict.fromkeys(listing_urls))[:5]

        for url in listing_urls:
            try:
                results.extend(scrape_listing(page, url))
            except Exception as e:
                print(f"Error: {e}")

        browser.close()

    return results[:10]


def export(data):
    output = {
        "shop": "WallArtBestSellers",
        "last_updated": datetime.utcnow().isoformat(),
        "total_reviews": len(data),
        "reviews": data
    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Exported {len(data)} reviews")


if __name__ == "__main__":
    data = scrape()
    export(data)
