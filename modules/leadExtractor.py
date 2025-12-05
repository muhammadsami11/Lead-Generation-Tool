from bs4 import BeautifulSoup
from modules.scrapinghandler import ScrapingHandler
from modules.Lead import Lead
import datetime
import requests
import re

class LeadExtractor:
    headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    # 1. FIX: Indentation starts here
    def clean_url(self, urls)->list[str]:
        try:
            cleaned_urls = []
            
            for url in urls:
                parse_result = requests.utils.urlparse(url)
                
                # 2. FIX: Set the path component to an empty string ('')
                clean_url = requests.utils.urlunparse((
                    parse_result.scheme, 
                    parse_result.netloc, 
                    '',  # <-- THIS MUST BE AN EMPTY STRING!
                    '', 
                    '', 
                    ''
                ))
                
                cleaned_urls.append(clean_url)
                
            return cleaned_urls # Return outside the loop, inside try block
            
        except Exception as e:
            print(f"Error in clean_url: {e}")
            return []
            
        finally:
            print("clean_url execution completed.")
    
    
    def extract_lead_info(self,result_block):
        # 3. FIX: Indentation for the second function starts here
        try:
            Leads=[]
            for url in result_block:
                try: # Use a nested try block for safe individual URL fetching
                    lead_instance=requests.get(url,headers=self.headers, timeout=10) 
                    
                    if lead_instance.status_code==200:
                        soup=BeautifulSoup(lead_instance.text,'html.parser')
                        title_tag=soup.find('title')
                        title=title_tag.text if title_tag else 'No Title Found'
                        email_find=soup.get_text()
                        email=re.findall(r'[a-z0-9]+@[a-z0-9\-\.]+\.(?:com|net|org|co|info|biz)', str(email_find), re.IGNORECASE) # Enhanced Regex
                        
                        lead_obj = Lead(
                            title=title,
                            email=email[0] if email else 'No Email Found',
                            website_url=url,
                            scraped_at=datetime.datetime.now().isoformat()
                        )
                        Leads.append(lead_obj)
                
                except requests.exceptions.RequestException as req_e:
                    print(f"❌ Network/Connection Error skipping URL {url}: {req_e}")
                    # Continue to the next URL in the loop
                    continue 

            return Leads
        
        except Exception as e:
            print(f"Error in extract_lead_info: {e}")
            return []
            
        finally:
            print("extract_lead_info execution completed.")

# Example usage:
# extractor = LeadExtractor()
# ScrapingHandler=ScrapingHandler()
# kw="Skincare products"
# links = ScrapingHandler.scrape_keyword(kw)
# extractor=LeadExtractor()
# result_blocks=extractor.clean_url(links)
# for url in result_blocks:
#     print(url)
# example_leads=extractor.extract_lead_info(result_blocks)
# for I in example_leads:
#     print(I.to_dict())