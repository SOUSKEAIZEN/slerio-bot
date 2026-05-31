import re
import urllib.parse
import requests
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
        logger.warning("URL Parser Warning: Received an empty or null URL input.")
        return result

    try:
        # Standardize URL formatting
        parsed_url = urllib.parse.urlparse(raw_url.strip())
        domain = parsed_url.netloc.lower()
        
        # Define supported domains using regex patterns
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
            logger.warning(u"URL Parser: Domain '%s' does not match any supported e-commerce platforms.", domain)
            return result
            
        logger.info(u"URL Parser: Detected supported store platform: %s", identified_store)
        
        # Clean tracking parameters based on platform specifications
        clean_url = ""
        if identified_store == "amazon":
            # Extract the core product ASIN path
            asin_match = re.search(r"(/dp/[A-Z0-9]{10}|/gp/product/[A-Z0-9]{10})", parsed_url.path, re.IGNORECASE)
            if asin_match:
                clean_url = f"https://www.amazon.in{asin_match.group(1)}"
            else:
                clean_url = f"https://{parsed_url.netloc}{parsed_url.path}"
                
        elif identified_store == "flipkart":
            # Flipkart needs the /p/ product ID path along with the 'pid' query parameter
            queries = urllib.parse.parse_qs(parsed_url.query)
            pid = queries.get("pid")
            if pid:
                clean_url = f"https://www.flipkart.com{parsed_url.path}?pid={pid[0]}"
            else:
                clean_url = f"https://www.flipkart.com{parsed_url.path}"
                
        else:
            # For Blinkit and Instamart, preserve base path and drop standard analytical trackers
            clean_url = f"https://{parsed_url.netloc}{parsed_url.path}"
            
        logger.info(u"URL Parser Success: Cleaned URL compiled: %s", clean_url)
        result["is_valid"] = True
        result["clean_url"] = clean_url
        result["store_type"] = identified_store
        return result

    except Exception as e:
        logger.error(u"URL Parser Failure: Error occurred while parsing link structure. Error: %s", str(e), exc_info=True)
        return result

def fetch_page_html(url: str) -> str:
    """
    Fetches the raw HTML content of a page using spoofed browser headers.
    Returns raw HTML string or None if the request fails or gets blocked.
    """
    logger.info(u"Scraper Engine: Initiating network fetch sequence for URL: %s", url)
    
    # Custom headers imitating a standard premium macOS desktop browser session
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        
        logger.info(u"Scraper Engine response status code: %s", response.status_code)
        
        if response.status_code == 200:
            logger.info("Scraper Engine Success: HTML page payload fully retrieved.")
            return response.text
        elif response.status_code == 503 or response.status_code == 403:
            logger.error(u"Scraper Engine Blocked: Platform returned a %s status (Anti-bot Captcha triggered).", response.status_code)
            return None
        else:
            logger.warning(u"Scraper Engine Warning: Network returned non-success status code: %s", response.status_code)
            return None
            
    except requests.exceptions.Timeout:
        logger.error("Scraper Engine Failure: Connection timed out while waiting for host response.")
        return None
    except Exception as e:
        logger.error(u"Scraper Engine Failure: Unexpected error during HTTP fetching. Error: %s", str(e), exc_info=True)
        return None

if __name__ == "__main__":
    # Local verification test execution
    print("Running standalone parser test execution...")
    test_url = "https://www.amazon.in/dp/B0CHX1W1XY?ref_=cm_sw_r_cp_ud_dp_123456&th=1"
    parsed_data = clean_and_identify_url(test_url)
    print(f"Parsed Output: {parsed_data}")