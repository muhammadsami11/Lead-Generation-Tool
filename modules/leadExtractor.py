import os
from bs4 import BeautifulSoup
import datetime
import requests
import re
import networkx as nx
import collections
import heapq
from urllib.parse import urlparse, urljoin
import datetime
import lxml
import random
import time
try:
    from .scrapinghandler import ScrapingHandler
    from .leadExtractor import LeadExtractor
    from .shared_log import log_status, LOG_QUEUE
    from .Lead import Lead
    from .email_utils import Email_Utils
except (ImportError, ValueError):
    import sys
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    from modules.scrapinghandler import ScrapingHandler
    from modules.keywordmodule import keywordmodule 
    from modules.shared_log import log_status, LOG_QUEUE
    from modules.Lead import Lead
    from modules.email_utils import Email_Utils
class LeadExtractor:
    user_agent_pool = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/120.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/120.0',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.15',
        'Mozilla/5.0 (Linux; Android 10; SM-G960F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
        'Mozilla/5.0 (Linux; Android 10; SM-G960F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Mobile Safari/537.36'
    ]


    cache={}
    BLACKLISTED_DOMAINS = [
    'apps.apple.com', 'play.google.com', 'www.reddit.com', 
    'substack.com', 'en.wikipedia.org', 'twitter.com', 
    'facebook.com', 'instagram.com', 'pinterest.com',
    'www.youtube.com', 'youtu.be', 'tiktok.com', 'linkedin.com',
    'www.amazon.com', 'www.ebay.com', 'www.etsy.com'
]
    MAX_VISITS=3
    MAX_DEPTH=2
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
            log_status(f"Error in clean_url: {e}")
            return []
            
        finally:
            log_status("clean_url execution completed.")
    
    
    def extract_lead_info(self,result_block):
        # 3. FIX: Indentation for the second function starts here
        try:
            Leads=[]
            for url in result_block:
                try: # Use a nested try block for safe individual URL fetching
                    selected_agent = random.choice(self.user_agent_pool)
                    dynamic_headers = {'User-Agent': selected_agent}
                    lead_instance=requests.get(url,headers=dynamic_headers, timeout=10) 
                    sleep_time = random.uniform(1, 4) 
                    time.sleep(sleep_time)
                    if lead_instance.status_code==200:
                        soup=BeautifulSoup(lead_instance.text,'html.parser')
                        title_tag=soup.find('title')
                        title=title_tag.text if title_tag else 'No Title Found'
                        # Instantiate Email_Utils and pass HTML text (lead_instance.text)
                        email = Email_Utils().extract_emails_from_html(lead_instance.text)

                        # Instagram extraction: ONLY from anchor hrefs (instagram.com or instagr.am)
                        # We intentionally removed regex/@-mention fallbacks to avoid noisy/non-link matches.
                        insta_id = None

                        for a_tag in soup.find_all('a', href=True):
                            href = a_tag['href']
                            if 'instagram.com' in href or 'instagr.am' in href:
                                try:
                                    parsed_inst = urlparse(href)
                                    # clean path and remove any trailing/query parts
                                    path = (parsed_inst.path or '').lstrip('/')
                                    candidate = path.split('/')[0].split('?')[0].split('#')[0].strip()
                                    # Filter out non-profile paths and noisy candidates
                                    blacklist = {'p', 'explore', 'about', 'accounts', 'developer', 'share', 'stories', 'tags', 'directory'}
                                    if candidate and len(candidate) <= 30 and re.match(r'^[A-Za-z0-9._]+$', candidate) and candidate.lower() not in blacklist and '.' not in candidate:
                                        insta_id = candidate
                                        break
                                except Exception:
                                    continue

                        lead_obj = Lead(
                            title=title,
                            email=email[0] if email else 'No Email Found',
                            website_url=url,
                            instagram_id=insta_id,
                            scraped_at=datetime.datetime.now().isoformat()
                        )
                        Leads.append(lead_obj)
                
                except requests.exceptions.RequestException as req_e:
                    log_status(f"❌ Network/Connection Error skipping URL {url}: {req_e}")
                    # Continue to the next URL in the loop
                    continue 

            return Leads
        
        except Exception as e:
            log_status(f"Error in extract_lead_info: {e}")
            return []
            
        finally:
            log_status("extract_lead_info execution completed.")
    def Make_A_Graph(self, url: str) -> nx.Graph:
        """
        Build a graph of internal links from the given URL.
        Returns an empty graph if timeout/network errors occur.
        """
        G = nx.Graph()
        
        try:
            parsed_url = urlparse(url)
            full_base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            base_url = parsed_url.netloc
            G.add_node(full_base_url)
            
            selected_agent = random.choice(self.user_agent_pool)
            dynamic_headers = {'User-Agent': selected_agent}      
            lead_instance = requests.get(full_base_url, headers=dynamic_headers, timeout=10)      
            
            if lead_instance.status_code == 200:
                soup = BeautifulSoup(lead_instance.text, 'html.parser')
                all_links = soup.find_all('a', href=True)
                for link in all_links:
                    url_address = urljoin(full_base_url, link['href'])
                    parsed_link_obj = urlparse(url_address)
                    condition = self.clean_all_urls(parsed_link_obj, base_url)
                    if condition:
                        clean_link = requests.utils.urlunparse((
                            parsed_link_obj.scheme,
                            parsed_link_obj.netloc,
                            '',
                            '',
                            '',
                            ''
                        ))
                        G.add_node(clean_link)
                        G.add_edge(full_base_url, clean_link)
        except requests.exceptions.Timeout:
            log_status(f"⏱️ Timeout while building graph for {url}. Returning empty graph.")
        except requests.exceptions.RequestException as req_e:
            log_status(f"❌ Network error building graph for {url}: {req_e}. Returning empty graph.")
        except Exception as e:
            log_status(f"❌ Error building graph for {url}: {e}. Returning empty graph.")
        
        return G
    def bfs(self,graph,start_node:str)->list[Lead]:
        visited=set()
        queue=[]
        max_visits=self.MAX_VISITS
        max_depth=self.MAX_DEPTH
        visits_count=0
        gnode=0
        hscore=self.calculate_heuristic(start_node,"")
        
        fcost=gnode+hscore
        if start_node in self.BLACKLISTED_DOMAINS:
            return None
        start_node=self.normalize_url_key(start_node)
        heapq.heappush( queue,(fcost,gnode,start_node))
        visited.add(start_node)
        while queue:
            fcost,current_depth,normalized_url=heapq.heappop(queue)
            log_status(f"Visiting: {normalized_url}")
            if current_depth >= max_depth:
                log_status(f"🛑 Max Depth ({max_depth}) reached at: {normalized_url}")
                continue # Skip processing this node and move to the next in the queue
            visits_count+=1
            if visits_count>max_visits:
                log_status(f"🛑 Max Visits ({max_visits}) reached. Ending search.")
                break
            extracted_leads=self.extract_lead_info([normalized_url])
            if extracted_leads:
                current_lead=extracted_leads[0]
                if self.lead_is_complete(current_lead):
                    return current_lead
            newly_discovered_neighbors_pairs = self.get_new_neighbors(normalized_url)
            for neighbor,neighbor_link_text in newly_discovered_neighbors_pairs:
                if neighbor not in visited:
                    gcostneighbor=current_depth+1
                    hcostneighbor=self.calculate_heuristic(neighbor,neighbor_link_text)
                    fneighbor=gcostneighbor+hcostneighbor
                    visited.add(neighbor)
                    heapq.heappush(queue,(fneighbor,gcostneighbor,neighbor))
                    
        return None

    def clean_all_urls(self,url_address,base_url:str)->bool:
           
            if url_address.netloc in self.BLACKLISTED_DOMAINS:
                return False
            if url_address.netloc!=base_url:
                return False
            if url_address.scheme not in ['http','https']:
                return False
            path=url_address.path.lower()
            if path.endswith(('.jpg','.png','.gif','.css','.js','.svg','.ico')):
                return False
            
            return True
    def intelligent_scraper(self, result_block) -> list[Lead]:
        """
        Intelligently scrape each URL in result_block.
        Skip individual URLs on timeout instead of crashing the entire batch.
        Will skip subsequent seed URLs from a domain after a lead (email) has been found there
        and returns a deduplicated list of leads (unique emails).
        """
        lead_list = []
        seen_domains = set()
        for url in result_block:
            try:
                parsed_seed = urlparse(url)
                seed_domain = parsed_seed.netloc

                if seed_domain in seen_domains:
                    log_status(f"⚠️ Skipping seed {url} because domain {seed_domain} already produced a lead.")
                    continue

                log_status(f"🔗 Processing seed URL: {url}")
                graph = self.Make_A_Graph(url)
                parsed_url = urlparse(url)
                full_base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

                lead = self.bfs(graph, full_base_url)

                # If BFS found a complete lead, record domain and append
                if lead is not None and self.lead_is_complete(lead):
                    lead_list.append(lead)
                    seen_domains.add(seed_domain)
                else:
                    lead_list.append(None)
            except requests.exceptions.Timeout as timeout_e:
                log_status(f"⏱️ Timeout on {url}: {str(timeout_e)[:80]}. Skipping to next URL...")
                lead_list.append(None)
            except requests.exceptions.RequestException as req_e:
                log_status(f"❌ Network error on {url}: {str(req_e)[:80]}. Skipping to next URL...")
                lead_list.append(None)
            except Exception as e:
                log_status(f"❌ Error processing {url}: {str(e)[:80]}. Skipping to next URL...")
                lead_list.append(None)
        
        # Deduplicate by email while preserving order
        unique_leads = []
        seen_emails = set()
        for lead in lead_list:
            if lead is None:
                continue
            email = getattr(lead, 'email', None)
            if not email:
                # keep leads with no email as they may still be useful
                unique_leads.append(lead)
                continue
            if email in seen_emails:
                log_status(f"🔁 Skipping duplicate lead with email: {email}")
                continue
            seen_emails.add(email)
            unique_leads.append(lead)

        return unique_leads
    
    def calculate_heuristic(self, url: str, link_text: str) -> int:
        """Estimates the remaining clicks (h(n)) to find the lead based on commercial footer data."""
        
        full_text = (url + " " + link_text).lower()
        
        # 1. IMMEDIATE GOAL INDICATORS (Cost: 1)
        if any(kw in full_text for kw in ['contact', 'contact-us','support', 'email', 'billing', 'shipment','privacy-policy', 'terms-of-service','about-us','terms-of-use']):
            return 1

        # 2. HIGH PROXIMITY TO GOAL (Cost: 2)
        # Customer Service, Affiliates, Returns are highly likely to contain contact info.
        if any(kw in full_text for kw in ['customer service', 'affiliates', 'returns', 'exchanges']):
            return 2

        # 3. MEDIUM PROXIMITY (Cost: 3)
        # General corporate information links.
        if any(kw in full_text for kw in ['careers', 'newsroom', 'community', 'team']):
            return 3

        # 4. LOW PROXIMITY / LEGAL (Cost: 4)
        # Standard legal/compliance pages.
        if any(kw in full_text for kw in ['privacy', 'legal', 'terms', 'accessibility']):
            return 4
            
        # 5. IRRELEVANT / COMMERCIAL CONTENT (Highest Penalty: 15)
        # These link to product/shopping pages, which are dead ends for leads.
        if any(kw in full_text for kw in [
            'blog', 'news', 'shop', 'product', 'gifts', 'sale', 'best-sellers', 
            'basket', 'checkout', 'login', 'rewards', 'auto-replenish', 'card'
        ]):
            return 15
            
        # 6. DEFAULT COST (Unspecified/Neutral Link: 10)
        # Forces A* to visit every single link above before visiting an unmarked link.
        return 10
    def get_new_neighbors(self, current_url: str) -> list[str]:
   
    # 1. Define the base domain (needed for filtering)
        internal_links = []
        normalized_url=self.normalize_url_key(current_url)
        parsed_base_url = urlparse(normalized_url)
        base_netloc = parsed_base_url.netloc
        full_base_url = f"{parsed_base_url.scheme}://{base_netloc}"
        try:
            if normalized_url in self.cache:
                log_status(f"Using cached content for: {normalized_url}")
                html_content=self.cache[normalized_url]
            else:
                try:
                    selected_agent = random.choice(self.user_agent_pool)
                    dynamic_headers = {'User-Agent': selected_agent}  
                    # 2. Fetch Content (using requests, assuming no Selenium needed here)
                    response = requests.get(normalized_url, headers=dynamic_headers, timeout=10)
                    response.raise_for_status()
                    html_content = response.text
                    self.cache[normalized_url]=html_content
                    sleep_time = random.uniform(2, 4) 
                    time.sleep(sleep_time)
                    # Check for HTTP errors 
                except requests.exceptions.RequestException as e:
                    log_status(f"❌ Error fetching {normalized_url}: {e}")
                    return []
            soup = BeautifulSoup(html_content, 'lxml')
            all_link_tags = soup.find_all('a', href=True)
                    
            # 3. Iterate, Normalize, and Filter Links
            for link_tag in all_link_tags:
                        # Normalize to an absolute URL
                url_address = urljoin(full_base_url, link_tag['href'])
                url_text=link_tag.get_text(strip=True)
                parsed_link_obj = urlparse(url_address)
                        
                # Use the cleaning method to check if the link is valid and internal
                if self.clean_all_urls(parsed_link_obj, base_netloc):
                            
                # Create the clean, scheme-prefixed link string for the queue
                    clean_link_string = requests.utils.urlunparse((
                    parsed_link_obj.scheme, 
                    parsed_link_obj.netloc, 
                    parsed_link_obj.path, # Keep the path for deeper traversal
                                    '', '', ''
                                ))
                    internal_links.append((clean_link_string,url_text))
            return internal_links
        except requests.exceptions.RequestException as e:
            log_status(f"❌ Failed to fetch links from {normalized_url}: {e}")
            return internal_links
        except Exception as e:
            log_status(f"❌ General error during neighbor discovery for {normalized_url}: {e}")
            return [] # Return an empty list for general errors too.
    def normalize_url_key(self, url: str) -> str:
        """Removes trailing slash to ensure consistent cache keys and visited set entries."""
        if url.endswith('/'):
            # Normalize by removing the trailing slash
            return url[:-1]
        return url
    def lead_is_complete(self, lead_obj: Lead) -> bool:
   
    
    # Check 1: Does the title/company name exist?
        if lead_obj.title in ('No Title Found', ''):
            return False

    # Check 2: Does it have a primary contact method?
        has_contact = (lead_obj.email != 'No Email Found' and lead_obj.email is not None)
        return has_contact
    # Create this new function inside your LeadExtractor class:

# Example usage:



# extractor = LeadExtractor()
# ScrapingHandler=ScrapingHandler()
# keywords=["veganskincare"]
# for kw in keywords:
#     links = ScrapingHandler.scrape_keyword(kw,max_results=10)
# final_lead=extractor.intelligent_scraper(links,5,2)
# for lead_obj in final_lead:
#     if lead_obj is not None:
#         # Call the .to_dict() method to see the actual contents of the object
#         log_status("--- EXTRACTED LEAD DATA ---")
#         log_status(lead_obj.to_dict()) 
#         log_status("---------------------------")
