"""
Re-scrape the product pages already in the catalog to refresh prices, stock and
other fields, without re-crawling the brand pages (so the set of parts stays the same).

Uses undetected-chromedriver (a visible Chrome window), which gets past PartSelect's
Cloudflare check without a click. Pages are parsed for the 2026 product-page layout.

Usage (from this folder):
    python refresh_parts.py            # scrape every catalog URL, then update the raw JSON files
    python refresh_parts.py --limit 5  # scrape at most 5 new URLs, then update
    python refresh_parts.py --only PS11738120 PS2121513
"""
import argparse
import json
import random
import re
import sys
import time
import winreg
from pathlib import Path

import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By

# Piped output on Windows falls back to cp1252, which can't print ✓ / ✗.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8")

HERE = Path(__file__).resolve().parent
RAW_DIR = HERE.parent / "partselect-backend" / "data" / "raw"
RAW_FILES = [RAW_DIR / "refrigerator_parts.json", RAW_DIR / "dishwasher_parts.json"]
CACHE_FILE = HERE / "scraped_data" / "refresh_cache.json"

# part_name comes from the brand listing page, so it is kept as is.
REFRESH_FIELDS = [
    "part_price", "availability", "brand", "mpn_id", "symptoms", "product_types",
    "replace_parts", "install_difficulty", "install_time", "install_video_url",
]
PAGE_WAIT = 45          # seconds for Cloudflare to clear and the product block to appear
DELAY = (3, 8)          # pause between pages, in seconds
MAX_FAILURES_IN_A_ROW = 5


def is_missing(value):
    return value in (None, "", "N/A")


def chrome_major_version():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon")
        return int(winreg.QueryValueEx(key, "version")[0].split(".")[0])
    except OSError:
        return None


def open_product_page(driver, url):
    """Load a product page and wait for Cloudflare to clear and the product block to render."""
    try:
        driver.get(url)
    except WebDriverException as e:
        print(f"  ✗ Navigation error: {e.msg}", flush=True)
        return False
    deadline = time.time() + PAGE_WAIT
    while time.time() < deadline:
        if driver.find_elements(By.CSS_SELECTOR, "div#main.pd[data-inventory-id]"):
            return True
        time.sleep(1)
    print(f"  ✗ No product page after {PAGE_WAIT}s (title: {driver.title!r})", flush=True)
    return False


def list_after_header(soup, header_text):
    header = soup.find("div", string=lambda s: s and s.strip().startswith(header_text))
    items = header.find_next("ul").find_all("li") if header else []
    return "\n".join(li.get_text(strip=True) for li in items)


def parse_product_page(html, url):
    soup = BeautifulSoup(html, "html.parser")
    main = soup.select_one("div#main.pd[data-inventory-id]")
    price = main.get("data-price", "")
    availability = soup.select_one("span[itemprop='availability']")
    replaces = soup.find("div", string=lambda s: s and "replaces these:" in s)
    replaces = replaces.find_next_sibling("div") if replaces else None
    rating = [p.get_text(strip=True) for p in soup.select(".pd__repair-rating__container__item p.bold")[:2]]
    video = soup.select_one("div.yt-video[data-yt-init]")
    return {
        "product_url": url,
        "part_id": f"PS{main['data-inventory-id']}",
        "part_price": f"{float(price):.2f}" if price else "",
        "mpn_id": main.get("data-mpn", ""),
        "brand": main.get("data-brand", ""),
        "availability": availability.get_text(strip=True) if availability else "",
        "symptoms": list_after_header(soup, "What this part fixes"),
        "product_types": list_after_header(soup, "Works with the following products"),
        "replace_parts": " ".join(replaces.get_text().split()) if replaces else "",
        "install_difficulty": rating[0] if len(rating) == 2 else "",
        "install_time": rating[1] if len(rating) == 2 else "",
        "install_video_url": f"https://www.youtube.com/watch?v={video['data-yt-init']}" if video else "",
    }


def load_cache():
    if CACHE_FILE.exists():
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    return {}


def save_cache(cache):
    CACHE_FILE.parent.mkdir(exist_ok=True)
    CACHE_FILE.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")


def is_complete(entry):
    return entry and not is_missing(entry.get("part_id")) and not is_missing(entry.get("part_price"))


def scrape(records, cache, limit, only):
    todo = []
    for r in records:
        url = r["product_url"]
        if only and r["part_id"] not in only:
            continue
        if url not in todo and not is_complete(cache.get(url)):
            todo.append(url)
    if limit:
        todo = todo[:limit]
    print(f"{len(todo)} product pages to scrape ({len(cache)} already cached)", flush=True)
    if not todo:
        return

    driver = uc.Chrome(headless=False, version_main=chrome_major_version())
    failures = 0
    try:
        for i, url in enumerate(todo, 1):
            print(f"[{i}/{len(todo)}] {url}", flush=True)
            if i > 1:
                time.sleep(random.uniform(*DELAY))
            loaded = open_product_page(driver, url)
            if not loaded:
                print("  Retrying once...", flush=True)
                time.sleep(random.uniform(10, 20))
                loaded = open_product_page(driver, url)
            if not loaded:
                failures += 1
                if failures >= MAX_FAILURES_IN_A_ROW:
                    print(f"✗ {failures} pages in a row failed; stopping (probably blocked)", flush=True)
                    break
                continue
            failures = 0
            try:
                data = parse_product_page(driver.page_source, url)
            except Exception as e:
                print(f"  ✗ Parse error: {e!r}", flush=True)
                continue
            print(f"  ✓ {data['part_id']} | ${data['part_price']} | {data['availability']}", flush=True)
            cache[url] = data
            save_cache(cache)
    finally:
        try:
            driver.quit()
        except OSError:
            pass


def apply(cache):
    """Write fresh fields back into the raw JSON files and report what changed."""
    changed, unchanged, skipped = [], 0, set()
    for path in RAW_FILES:
        records = json.loads(path.read_text(encoding="utf-8"))
        for r in records:
            fresh = cache.get(r["product_url"])
            if not is_complete(fresh):
                skipped.add(r["part_id"])
                continue
            if fresh["part_id"] != r["part_id"]:
                # The URL now resolves to a different part; don't attach its price to this one.
                print(f"  ⚠ {r['part_id']}: page shows {fresh['part_id']}, left unchanged")
                skipped.add(r["part_id"])
                continue
            old_price = r["part_price"]
            for field in REFRESH_FIELDS:
                if not is_missing(fresh.get(field)):
                    r[field] = fresh[field]
            if r["part_price"] != old_price:
                changed.append((r["part_id"], r["part_name"], old_price, r["part_price"]))
            else:
                unchanged += 1
        path.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\nRecords with a new price: {len(changed)}, same price: {unchanged}, "
          f"parts not refreshed: {len(skipped)}")
    for part_id, name, old, new in sorted(set(changed)):
        print(f"  {part_id}  {name}: ${old or '?'} -> ${new}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--limit", type=int, default=0, help="scrape at most N new URLs")
    parser.add_argument("--only", nargs="+", default=[], help="only these part numbers")
    args = parser.parse_args()

    records = [r for path in RAW_FILES for r in json.loads(path.read_text(encoding="utf-8"))]
    cache = load_cache()
    scrape(records, cache, args.limit, set(args.only))
    apply(cache)


if __name__ == "__main__":
    main()
