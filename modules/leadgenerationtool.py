from typing import TypeVar
import os
import threading
import time
try:
    from .scrapinghandler import ScrapingHandler
    from .leadExtractor import LeadExtractor
    from .database_manager import DatabaseManager 
    from .keywordmodule import keywordmodule
    from .LeadValidator import LeadValidator
    from .shared_log import log_status, LOG_QUEUE
    from .Lead import Lead
except (ImportError, ValueError):
    import sys
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    from modules.scrapinghandler import ScrapingHandler
    from modules.leadExtractor import LeadExtractor
    from modules.database_manager import DatabaseManager 
    from modules.keywordmodule import keywordmodule 
    from modules.LeadValidator import LeadValidator
    from modules.shared_log import log_status, LOG_QUEUE
    from modules.Lead import Lead
# Define the type alias for clarity
StorageType = TypeVar('StorageType', bound=DatabaseManager)

class LeadGenerationTool:
    def __init__(self, input_module: keywordmodule, scraper: ScrapingHandler, storage: StorageType, extractor: LeadExtractor = None, validator: LeadValidator = None):
        """
        Initializes the tool with dependencies.
        - `extractor` is optional; if not provided, an extractor can be passed per-call to `process_keyword` via `extractor_instance`.
        - The storage dependency is the persistent DatabaseManager.
        - The validator is optional; when provided it will be used to validate leads before storage.
        """
        self.input_module = input_module
        self.scraper = scraper
        self.storage = storage 
        self.extractor = extractor
        self.validator = validator
        log_status("🔧 LeadGenerationTool initialized.")

    def process_keyword(self, keyword: str, extractor_instance: LeadExtractor = None, max_seed_urls: int = 3, MAX_DEPTH: int = 2, MAX_VISITS=3) -> list[Lead]:
        """
        Processes a single keyword: scrapes, extracts leads, and stores them.
        - `extractor_instance` may be provided to override the instance stored on the tool. If omitted, `self.extractor` will be used.
        Retries on timeout/network errors instead of crashing the entire thread.
        Returns the list of newly extracted Leads (objects).
        """
        for attempt in range(MAX_DEPTH + 1):
            try:
                # 1. Scrape the content -> Use the passed parameter for flexibility
                log_status(f"🔍 Starting search and scraping for seed URLs for '{keyword}'... (attempt {attempt + 1}/{MAX_DEPTH + 1})")
                clean_urls = self.scraper.scrape_keyword(keyword)

                if not clean_urls:
                    log_status(f"🛑 Skipping keyword '{keyword}' due to failed scrape (no seed URLs found).")
                    return []

                # 2. Choose extractor (instance param overrides internal extractor)
                extractor_to_use = extractor_instance or self.extractor
                if extractor_to_use is None:
                    log_status(f"🛑 No extractor available to process keyword '{keyword}'.")
                    return []

                # 3. Extract results
                log_status(f"🧩 Starting intelligent crawling and extraction from {len(clean_urls)} seed URLs...")

                extracted_leads = extractor_to_use.intelligent_scraper(clean_urls)
                
                valid_leads = [lead for lead in extracted_leads if lead is not None]

                # Optional validation step (only if a validator was provided)
                if self.validator and valid_leads:
                    try:
                        for lead in valid_leads:
                            # validator may modify lead in-place (sets is_lead_valid etc.)
                            self.validator.validate_lead(lead)
                    except Exception as e:
                        log_status(f"⚠️ Lead validation error: {e}")

                # 4. Store the extracted leads using the DatabaseManager
                if valid_leads:
                    count = self.storage.add_all_leads(valid_leads) 
                    log_status(f"✅ Successfully extracted and stored {count} leads for '{keyword}'.")
                else:
                    log_status(f"⚠️ No leads extracted for '{keyword}'.")
                    
                return valid_leads # Return the data collected
                
            except Exception as e:
                if attempt < MAX_DEPTH:
                    log_status(f"⚠️ Timeout/Error on attempt {attempt + 1}: {str(e)[:100]}... Retrying...")
                else:
                    log_status(f"⚠️ Skipping keyword '{keyword}' after {MAX_DEPTH + 1} attempts. Last error: {str(e)[:100]}")
                    return []
        
        return []
# if __name__ == "__main__":
#     # Initialize dependencies
#     input_module = keywordmodule()
#     scraper = ScrapingHandler()
    
#     # 💥 FIX: Initialize the permanent DatabaseManager instead of TemporaryStorage
#     storage = DatabaseManager()
#     extractor = LeadExtractor()
    
#     # Get user input and set the keywords list
#     search_keyword=input("Enter your keywords separated by commas: ")
#     input_module.keywords=search_keyword.split(",") 

    
#     # Pass dependencies to the constructor (extractor is optional but provided here)
#     lead_tool = LeadGenerationTool(
#         input_module=input_module, 
#         scraper=scraper, 
#         storage=storage,
#         extractor=extractor
#     )

#     # Start a console log_statuser to show queued backend logs in real-time
#     stop_event = threading.Event()
#     def _log_statuser():
#         while not stop_event.is_set() or not LOG_QUEUE.empty():
#             try:
#                 msg = LOG_QUEUE.get(timeout=0.5)
#                 log_status(msg)
#             except Exception:
#                 continue

#     t = threading.Thread(target=_log_statuser, daemon=True)
#     t.start()

#     # Run the lead generation process (uses input_module.keywords set above)
#     lead1=lead_tool.process_keyword(search_keyword, extractor_instance=extractor)
#     log_status(f"\nExtracted {len(lead1)} leads for keyword '{search_keyword}'.")    

#     leads_in_db = storage.get_all_leads()
#     log_status(f"Total leads stored in database: {len(leads_in_db)}")
#     for lead in leads_in_db:
#         log_status(f"- {lead.email} (Valid: {lead.website_url})")
#     # Stop the log_statuser and drain remaining logs
#     stop_event.set()
#     t.join()

   