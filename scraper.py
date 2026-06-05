import re
import urllib.parse
import requests
from bs4 import BeautifulSoup
from logger import logger

def clean_and_identify_url(raw_url: str) -> dict:
    """
    Parses a raw URL, strips tracking parameters, and identifies the e-commerce store.
    Returns a dictionary containing the clean URL, store type, and validity status.
    """
    logger.info(u"URL Parser: Analyzing raw input link: %s", raw_url)
    
    result = {
        "is_valid": False,
        "clean_url": None,
        "store_type": None
    }
    
    if not raw_url:
        return result

    try:
        parsed_url = urllib.parse.urlparse(raw_url.strip())
        domain = parsed_url.netloc.lower()
        
        store_patterns = {
            "amazon": r"(www\.)?amazon\.(in|com)",
            "flipkart": r"(www\.)?flipkart\.com",
            "blinkit": r"(www\.)?blinkit\.com",
            "instamart": r"(www\.)?swiggy\.com/instamart"
        }
        
        identified_store = None
        for store, pattern in store_patterns.items():
            if re.search(pattern, domain) or (store == "instamart" and "swiggy.com/instamart" in parsed_url.path.lower()):
                identified_store = store
                break
                
        if not identified_store:
            return result
            
        clean_url = ""
        if identified_store == "amazon":
            asin_match = re.search(r"(/dp/[A-Z0-9]{10}|/gp/product/[A-Z0-9]{10})", parsed_url.path, re.IGNORECASE)
            if asin_match:
                clean_url = f"https://www.amazon.in{asin_match.group(1)}"
            else:
                clean_url = f"https://{parsed_url.netloc}{parsed_url.path}"
                
        elif identified_store == "flipkart":
            queries = urllib.parse.parse_qs(parsed_url.query)
            pid = queries.get("pid")
            if pid:
                clean_url = f"https://www.flipkart.com{parsed_url.path}?pid={pid[0]}"
            else:
                clean_url = f"https://www.flipkart.com{parsed_url.path}"
                
        else:
            clean_url = f"https://{parsed_url.netloc}{parsed_url.path}"
            
        result["is_valid"] = True
        result["clean_url"] = clean_url
        result["store_type"] = identified_store
        return result

    except Exception as e:
        logger.error(u"URL Parser Failure: Error parsing link. Error: %s", str(e), exc_info=True)
        return result

def fetch_page_html(url: str) -> str:
    """
    Fetches the raw HTML content of a page using spoofed browser headers.
    """
    logger.info(u"Scraper Engine: Initiating network fetch sequence for URL: %s", url)
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Cache-Control": "max-age=0"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            logger.info("Scraper Engine Success: HTML page payload fully retrieved.")
            return response.text
        else:
            logger.warning(u"Scraper Engine Warning: Network returned status code: %s", response.status_code)
            return None
    except Exception as e:
        logger.error(u"Scraper Engine Failure: Fetch error. Error: %s", str(e), exc_info=True)
        return None

def extract_price_and_name(html: str, store_type: str) -> dict:
    """
    Parses HTML using BeautifulSoup to extract the product name and current price.
    """
    logger.info(u"Data Extractor: Parsing HTML structure for %s...", store_type)
    soup = BeautifulSoup(html, "html.parser")
    
    result = {
        "name": "Unknown Product",
        "price": None
    }
    
    try:
        if store_type == "amazon":
            # Extract Amazon Product Name
            title_element = soup.find(id="productTitle")
            if title_element:
                result["name"] = title_element.get_text(strip=True)[:100]
                
            # Extract Amazon Price (usually wrapped in 'a-price-whole' or 'a-offscreen')
            price_element = soup.find("span", class_="a-price-whole") or soup.find("span", class_="a-offscreen")
            if price_element:
                raw_price = price_element.get_text(strip=True)
                clean_price = re.sub(r"[^\d.]", "", raw_price)
                if clean_price:
                    result["price"] = float(clean_price)

        elif store_type == "flipkart":
            # Extract Flipkart Product Name
            title_element = soup.find("span", class_="B_NuCI") or soup.find("span", class_="VU-ZEz")
            if title_element:
                result["name"] = title_element.get_text(strip=True)[:100]
                
            # Extract Flipkart Price
            price_element = soup.find("div", class_=re.compile(r"(_30jeq3|Nx9w9m|CxhGGd)"))
            if price_element:
                raw_price = price_element.get_text(strip=True)
                clean_price = re.sub(r"[^\d.]", "", raw_price)
                if clean_price:
                    result["price"] = float(clean_price)
                    
        # Fallback for name if scraping fails
        if result["name"] == "Unknown Product":
            result["name"] = f"Tracked Item ({store_type.capitalize()})"
            
        if result["price"]:
            logger.info(u"Data Extractor Success: Found '%s' at ₹%s", result["name"], result["price"])
        else:
            logger.warning("Data Extractor Warning: Could not locate price tags in HTML.")
            
    except Exception as e:
        logger.error(u"Data Extractor Failure: Parsing crashed. Error: %s", str(e), exc_info=True)
        
    return result

if __name__ == "__main__":
    print("Running standalone scraper test execution...")
    test_url = "https://www.amazon.in/dp/B0CHX1W1XY"
    print(f"Fetching: {test_url}")
    html_data = fetch_page_html(test_url)
    if html_data:
        extracted = extract_price_and_name(html_data, "amazon")
        print(f"Extraction Result: {extracted}"