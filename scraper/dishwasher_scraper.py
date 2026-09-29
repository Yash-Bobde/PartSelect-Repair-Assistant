import requests
from bs4 import BeautifulSoup
import csv
import json
import time
import random
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException, NoSuchElementException, WebDriverException
import urllib.parse
import socket

def wait_and_find_element(driver, by, value, timeout=10):
    """Helper function to wait for an element and handle stale element exceptions"""
    wait = WebDriverWait(driver, timeout)
    try:
        element = wait.until(EC.presence_of_element_located((by, value)))
        return element
    except (TimeoutException, StaleElementReferenceException):
        return None


def wait_and_find_elements(driver, by, value, timeout=10):
    """Helper function to wait for elements and handle stale element exceptions"""
    wait = WebDriverWait(driver, timeout)
    try:
        elements = wait.until(EC.presence_of_all_elements_located((by, value)))
        return elements
    except (TimeoutException, StaleElementReferenceException):
        return []


def safe_get_text(element):
    """Safely get text from an element, handling stale element exceptions"""
    try:
        return element.text
    except StaleElementReferenceException:
        return "N/A"


def safe_get_attribute(element, attribute):
    """Safely get attribute from an element, handling stale element exceptions"""
    try:
        return element.get_attribute(attribute)
    except StaleElementReferenceException:
        return "N/A"
    

def is_valid_url(url):
    """Check if a URL is valid and can be resolved"""
    try:
        parsed_url = urllib.parse.urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            return False
        socket.gethostbyname(parsed_url.netloc)
        return True
    except (ValueError, socket.gaierror):
        return False


def safe_navigate(driver, url, max_retries=3):
    """Safely navigate to a URL with retries and ensure page is fully loaded"""
    for attempt in range(max_retries):
        try:
            # Add random delay to appear more human (3-8 seconds)
            delay = random.uniform(3, 8)
            print(f"Waiting {delay:.1f}s before navigation...")
            time.sleep(delay)
            
            print(f"Navigating to {url} (attempt {attempt+1}/{max_retries})")
            driver.get(url)
            
            # Wait for document ready state to be complete
            wait = WebDriverWait(driver, 30)
            wait.until(lambda driver: driver.execute_script('return document.readyState') == 'complete')
            
            # Determine if this is a product page or category page based on URL
            is_product_page = "/PS" in url or ".htm" not in url
            
            # Wait for key elements that indicate the page has loaded
            try:
                if is_product_page:
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.pd__wrap")))
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "span.price.pd__price")))
                else:
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.container")))
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "nf__links")))
                
                print(f"✓ Page loaded successfully")
                return True
                
            except TimeoutException as e:
                print(f"Timeout waiting for key elements: {str(e)}")
                if attempt < max_retries - 1:
                    print("Retrying...")
                    time.sleep(5)
                continue
                
        except WebDriverException as e:
            print(f"Navigation error (attempt {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                print("Retrying after error...")
                time.sleep(5)
            else:
                print(f"✗ Failed to navigate after {max_retries} attempts")
                return False
    
    return False


def extract_text_after_header(element, header_text):
    """Extract text after a header in an element"""
    try:
        full_text = safe_get_text(element)
        if header_text in full_text:
            return full_text.replace(header_text, "").strip()
        return full_text
    except Exception:
        return "N/A"


def scrape_part_info(driver, part_name, product_url):
    """Scrape information for a specific part from its product page."""
    data = {
        'part_name': part_name,
        'part_id': 'N/A',
        'mpn_id': 'N/A',
        'part_price': 'N/A',
        'install_difficulty': 'N/A',
        'install_time': 'N/A',
        'symptoms': 'N/A',
        'product_types': 'N/A',
        'replace_parts': 'N/A',
        'brand': 'N/A',
        'availability': 'N/A',
        'install_video_url': 'N/A',
        'product_url': product_url
    }
    
    if not safe_navigate(driver, product_url):
        print(f"✗ Failed to navigate to product {part_name}")
        return data
    
    # Extract all data fields (same as before)
    product_id_elements = wait_and_find_elements(driver, By.CSS_SELECTOR, "span[itemprop='productID']")
    if product_id_elements:
        data['part_id'] = safe_get_text(product_id_elements[0])
    
    brand_element = wait_and_find_element(driver, By.CSS_SELECTOR, "span[itemprop='brand'] span[itemprop='name']")
    if brand_element:
        data['brand'] = safe_get_text(brand_element)
    
    availability_element = wait_and_find_element(driver, By.CSS_SELECTOR, "span[itemprop='availability']")
    if availability_element:
        data['availability'] = safe_get_text(availability_element)
    
    video_container = wait_and_find_element(driver, By.CSS_SELECTOR, "div.yt-video")
    if video_container:
        video_id = safe_get_attribute(video_container, "data-yt-init")
        if video_id:
            data['install_video_url'] = f"https://www.youtube.com/watch?v={video_id}"
    
    mpn_elements = wait_and_find_elements(driver, By.CSS_SELECTOR, "span[itemprop='mpn']")
    if mpn_elements:
        data['mpn_id'] = safe_get_text(mpn_elements[0])
    
    replace_parts_elements = wait_and_find_elements(driver, By.CSS_SELECTOR, "div[data-collapse-container='{\"targetClassToggle\":\"d-none\"}']")
    if replace_parts_elements:
        data['replace_parts'] = safe_get_text(replace_parts_elements[0])
    
    wait = WebDriverWait(driver, 10)
    try:
        price_container = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "span.price.pd__price")))
        if price_container:
            time.sleep(1)
            price_element = price_container.find_element(By.CSS_SELECTOR, "span.js-partPrice")
            if price_element:
                data['part_price'] = safe_get_text(price_element)
    except:
        pass
    
    pd_wrap = wait_and_find_element(driver, By.CSS_SELECTOR, "div.pd__wrap.row")
    if pd_wrap:
        info_divs = pd_wrap.find_elements(By.CSS_SELECTOR, "div.col-md-6.mt-3")
        for div in info_divs:
            header = div.find_element(By.CSS_SELECTOR, "div.bold.mb-1")
            if not header:
                continue
            header_text = safe_get_text(header)
            if "This part fixes the following symptoms:" in header_text:
                data['symptoms'] = extract_text_after_header(div, header_text)
            elif "This part works with the following products:" in header_text:
                data['product_types'] = extract_text_after_header(div, header_text)
    
    install_container = wait_and_find_element(driver, By.CSS_SELECTOR, "div.d-flex.flex-lg-grow-1.col-lg-7.col-12.justify-content-lg-between.mt-lg-0.mt-2")
    if install_container:
        d_flex_divs = install_container.find_elements(By.CLASS_NAME, "d-flex")
        if len(d_flex_divs) >= 2:
            difficulty_p = d_flex_divs[0].find_element(By.TAG_NAME, "p")
            if difficulty_p:
                data['install_difficulty'] = safe_get_text(difficulty_p)
            time_p = d_flex_divs[1].find_element(By.TAG_NAME, "p")
            if time_p:
                data['install_time'] = safe_get_text(time_p)
    
    print(f"✓ Scraped: {data['part_name']} | Price: {data['part_price']} | ID: {data['part_id']}")
    return data


def process_category_page(driver, link_url):
    """Process a category page and scrape all parts within it."""
    parts_data = []
    print(f"\n{'='*60}")
    print(f"Processing category: {link_url}")
    print(f"{'='*60}")
    
    if not safe_navigate(driver, link_url):
        print(f"✗ Failed to navigate to category")
        return parts_data
    
    part_divs = wait_and_find_elements(driver, By.CSS_SELECTOR, "div.nf__part.mb-3")
    if not part_divs:
        print(f"✗ No parts found in category")
        return parts_data
        
    print(f"Found {len(part_divs)} parts in category")
    
    part_info = []
    for part_div in part_divs:
        try:
            a_tag = part_div.find_element(By.CLASS_NAME, "nf__part__detail__title")
            if not a_tag:
                continue
            part_name = safe_get_text(a_tag.find_element(By.TAG_NAME, "span"))
            href = safe_get_attribute(a_tag, "href")
            if href and is_valid_url(href):
                part_info.append((part_name, href))
        except:
            continue
    
    if not part_info:
        print(f"✗ No valid parts found")
        return parts_data
    
    print(f"Processing {len(part_info)} parts...")
    for idx, (part_name, product_url) in enumerate(part_info, 1):
        print(f"\n[{idx}/{len(part_info)}] Processing: {part_name}")
        part_data = scrape_part_info(driver, part_name, product_url)
        parts_data.append(part_data)
        
        # Add delay between parts
        time.sleep(random.uniform(5, 10))
        
        if not safe_navigate(driver, link_url):
            print(f"✗ Failed to return to category. Stopping.")
            break
    
    return parts_data


def setup_driver():
    """Set up and return a configured Chrome driver with anti-detection."""
    try:
        print("Setting up Chrome with anti-detection...")
        chrome_options = Options()
        
        # Stealth options
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Realistic user agent
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        ]
        chrome_options.add_argument(f'user-agent={random.choice(user_agents)}')
        
        # Exclude automation flags
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Additional prefs
        prefs = {
            "profile.default_content_setting_values.notifications": 2,
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        print("Initializing Chrome driver...")
        driver = webdriver.Chrome(options=chrome_options)
        print("✓ Chrome driver initialized")
        
        driver.set_page_load_timeout(60)
        driver.set_script_timeout(30)
        
        # Stealth JavaScript
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                window.chrome = {runtime: {}};
            '''
        })
        
        return driver
        
    except Exception as e:
        print(f"✗ Failed to create driver: {str(e)}")
        raise


def save_brand_data(brand_data, brand_name, output_dir="scraped_data"):
    """Save data for a single brand to both CSV and JSON formats."""
    if not brand_data:
        return
    
    os.makedirs(output_dir, exist_ok=True)
    clean_brand_name = brand_name.replace(" ", "_").replace("/", "-")
    
    try:
        csv_filename = os.path.join(output_dir, f"{clean_brand_name}.csv")
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=brand_data[0].keys())
            writer.writeheader()
            writer.writerows(brand_data)
        print(f"✓ Saved CSV: {csv_filename}")
        
        json_filename = os.path.join(output_dir, f"{clean_brand_name}.json")
        with open(json_filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(brand_data, jsonfile, indent=2, ensure_ascii=False)
        print(f"✓ Saved JSON: {json_filename}")
        
    except Exception as e:
        print(f"✗ Error saving data: {e}")


def process_brand(brand_url, max_retries=3):
    """Process a brand page and its related pages."""
    brand_name = brand_url.split("/")[-1].replace("-Refrigerator-Parts.htm", "")
    brand_parts_data = []
    driver = None
    
    for attempt in range(max_retries):
        try:
            driver = setup_driver()
            
            if not safe_navigate(driver, brand_url):
                if driver:
                    driver.quit()
                continue
            
            print(f"\n{'#'*60}")
            print(f"# BRAND: {brand_name}")
            print(f"{'#'*60}")
            
            brand_data = process_category_page(driver, brand_url)
            brand_parts_data.extend(brand_data)
            print(f"✓ Found {len(brand_data)} products on brand page")
            
            driver.quit()
            return brand_name, brand_parts_data
            
        except Exception as e:
            print(f"✗ Attempt {attempt + 1} failed: {e}")
            if driver:
                driver.quit()
            if attempt < max_retries - 1:
                time.sleep(10)
    
    return brand_name, brand_parts_data


def get_brand_links(driver, base_url):
    """Get all brand links from the main page"""
    brand_links = []
    if not safe_navigate(driver, base_url):
        return brand_links

    try:
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "nf__links")))
        ul_tags = driver.find_elements(By.CLASS_NAME, "nf__links")
        if ul_tags:
            li_tags = ul_tags[0].find_elements(By.TAG_NAME, "li")
            print(f"Found {len(li_tags)} brand links")
            
            for li_tag in li_tags:
                try:
                    a_tag = li_tag.find_element(By.TAG_NAME, "a")
                    link_url = safe_get_attribute(a_tag, "href")
                    if link_url and is_valid_url(link_url):
                        brand_links.append(link_url)
                        print(f"  • {link_url}")
                except:
                    continue
    except Exception as e:
        print(f"✗ Error finding brand links: {e}")
    
    return brand_links


def scrape_all_parts(base_url, max_brands=10):
    """Scrape all parts with incremental saving and limit to first N brands."""
    all_parts_data = []
    driver = None
    brand_links = []
    
    try:
        print("\n" + "="*60)
        print("STARTING SCRAPER")
        print("="*60)
        
        driver = setup_driver()
        print("\nGathering brand links...")
        brand_links = get_brand_links(driver, base_url)
        driver.quit()
        driver = None
        
        if not brand_links:
            print("✗ No brand links found")
            return all_parts_data
        
        brand_links = brand_links[10]
        print(f"\n{'='*60}")
        print(f"Processing {len(brand_links)} brands")
        print(f"{'='*60}\n")
        
        for idx, brand_url in enumerate(brand_links, 1):
            print(f"\n\n{'*'*60}")
            print(f"* BRAND {idx}/{len(brand_links)}")
            print(f"{'*'*60}")
            
            try:
                brand_name, brand_data = process_brand(brand_url)
                
                if brand_data:
                    save_brand_data(brand_data, brand_name)
                    all_parts_data.extend(brand_data)
                    print(f"\n✓ Completed {idx}/{len(brand_links)}: {brand_name} ({len(brand_data)} parts)")
                else:
                    print(f"\n⚠ No data for: {brand_name}")
                
                # Delay between brands
                if idx < len(brand_links):
                    delay = random.uniform(15, 30)
                    print(f"\nWaiting {delay:.1f}s before next brand...")
                    time.sleep(delay)
                    
            except Exception as e:
                print(f"\n✗ Error processing brand: {e}")
                continue
    
    except Exception as e:
        print(f"✗ Error during scraping: {e}")
    
    finally:
        if driver:
            driver.quit()
    
    print(f"\n\n{'='*60}")
    print(f"SCRAPING COMPLETE!")
    print(f"Brands processed: {len(brand_links)}")
    print(f"Total parts: {len(all_parts_data)}")
    print(f"{'='*60}\n")
    return all_parts_data


if __name__ == "__main__":
    base_url = "https://www.partselect.com/Refrigerator-Parts.htm"
    print("\n🚀 Starting refrigerator parts scraper (first 10 brands)...")
    
    parts_data = scrape_all_parts(base_url, max_brands=10)
    
    if parts_data:
        print("\nSaving consolidated files...")
        
        with open("dishwasher_parts_consolidated.csv", 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=parts_data[0].keys())
            writer.writeheader()
            writer.writerows(parts_data)
        print("✓ Saved: dishwasher_parts_consolidated.csv")
        
        with open("dishwasher_parts_consolidated.json", 'w', encoding='utf-8') as f:
            json.dump(parts_data, f, indent=2, ensure_ascii=False)
        print("✓ Saved: dishwasher_parts_consolidated.json")
        
        print(f"\n✅ SUCCESS! Scraped {len(parts_data)} total parts")
        print(f"📁 Individual brand files: ./scraped_data/")
    else:
        print("\n⚠️ No data was collected")