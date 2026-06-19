import json
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright

SHOP_URL = "https://www.etsy.com/shop/WallArtBestSellers"

output_dir = Path("output")
output_dir.mkdir(exist_ok=True)


def get_listing_urls(page):
    page.goto(SHOP_URL, timeout=60000)
    page.wait_for_timeout(3000)

    listings = page.locator("a[href*='/listing/']").all()
    urls = []

    for l in listings:
        href = l.get_attribute("href")
        if href and "/listing/" in href:
            if href.startswith("/"):
                href = "https://www.etsy.com" + href
            urls.append(href)

    # dedupe
    return list(set(urls))[:5]


def scrape_reviews_from_listing(page, url):
    reviews = []

    page.goto(url, timeout=60000)
    page.wait_for_timeout(3000)

    # scroll to trigger review loading
    for _ in range(3):
        page.mouse.wheel(0, 1500)
        page.wait_for_timeout(1500)

    # Etsy review blocks (more targeted attempt)
    blocks = page.locator("div[data-review-id], div.review, section").all()

    for b in blocks:
        text = b.inner_text().strip()

        if len(text) > 30 and len(text) < 500:
            reviews.append({
                "reviewer": "Etsy Customer",
                "rating": 5,
                "text": text,
                "date": "",
                "listing": url,
                "etsy_url": url
            })

    return reviews[:3]


def scrape():
    all_reviews = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        listing_urls = get_listing_urls(page)

        print(f"Found listings: {len(listing_urls)}")

        for url in listing_urls:
            try:
                reviews = scrape_reviews_from_listing(page, url)
                all_reviews.extend(reviews)
            except Exception as e:
                print(f"Error on {url}: {e}")

        browser.close()

    return all_reviews[:10]


reviews = scrape()

data = {
    "shop": "WallArtBestSellers",
    "last_updated": datetime.utcnow().isoformat(),
    "total_reviews": len(reviews),
    "reviews": reviews
}

with open(output_dir / "reviews.json", "w") as f:
    json.dump(data, f, indent=2)

print(f"Scraped {len(reviews)} reviews")
