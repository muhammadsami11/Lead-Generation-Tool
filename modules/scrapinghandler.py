from urllib.parse import urlparse
import re
from urllib.parse import parse_qs, unquote, urlparse
import requests
from typing import Optional, Dict, TYPE_CHECKING
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.common.by import By
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
try:
    
    from .shared_log import log_status, LOG_QUEUE
    
except (ImportError, ValueError):
    import sys
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    from modules.shared_log import log_status, LOG_QUEUE
## 1. ScrapingHandler Class (Maira's Task)

class ScrapingHandler:
    """
    Handles the web scraping process, making requests and returning
    the raw HTML content.
    """
    MAX_RESULTS=20
    BASE_URL: str = "https://duckduckgo.com/?q="  # Placeholder URL
    HEADERS: Dict[str, str] = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    def __init__(self, base_url: str = BASE_URL, headers: Dict[str, str] = HEADERS):
        """Initializes the ScrapingHandler."""
        self.BASE_URL = base_url
        self.HEADERS = headers

    def make_request(self, url: str,max_results: int) -> list[str]:
        """
        Performs an HTTP GET request to the given URL and returns the HTML content.
        """
        try:
            options=Options()
            driver = webdriver.Firefox(options=options)

            driver.get(url)
            time.sleep(1)
            try:
                alert = driver.switch_to.alert
                alert.accept()
                log_status("Alert accepted")
            except:
                pass
            WebDriverWait(driver, 8).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'a[href^="http"]:not([href*="duckduckgo.com"])')
            )
             )

            time.sleep(1)
            max_scrolls = 5
            last_height = driver.execute_script("return document.body.scrollHeight")
            for _ in range(max_scrolls):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1.2)
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
             # Wait for JavaScript to load content
            links = driver.find_elements(By.CSS_SELECTOR, 'a[href^="http"]:not([href*="duckduckgo.com"])')
            link_to_process=links[:max_results]
            results = []
            for link in link_to_process:
                href = link.get_attribute("href")

                if "uddg=" in href:  # if DuckDuckGo redirect
                    parsed = urlparse(href)
                    qs = parse_qs(parsed.query)
                    if "uddg" in qs:
                        href = unquote(qs["uddg"][0])

                if href.startswith("http") and "duckduckgo.com" not in href and href not in results:
                    results.append(href)
                log_status(f"✅ Found {len(results)} real URLs")
            return results
        
        except requests.exceptions.RequestException as e:
            log_status(f"❌ Request Error for {url}: {e}")
            return None
        finally:
            driver.quit()

    def scrape_keyword(self, keyword: str ) -> list[str]:
        """
        Constructs the search URL for a given keyword and fetches the HTML content.
        """
        try:
                search_query = requests.utils.quote(keyword)
                full_url = f"{self.BASE_URL}{search_query}"
                
                log_status(f"🔍 Starting scrape for keyword: '{keyword}'")
                
                return self.make_request(full_url,self.MAX_RESULTS)
        except Exception as e:
                log_status(f"❌ Error during scraping for keyword '{keyword}': {e}")
                return None
    


# # Example usage:
# scraper = ScrapingHandler()
# html_content = scraper.scrape_keyword("Fragrance",max_results=20)
# for i in html_content:
#     log_status(i)

