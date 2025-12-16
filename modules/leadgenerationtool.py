from modules.scrapinghandler import ScrapingHandler
from modules.Lead import Lead
from modules.leadExtractor import LeadExtractor
# 💥 CRITICAL FIX: Replace TemporaryStorage with the permanent DatabaseManager
from modules.database_manager import DatabaseManager 
from modules.keywordmodule import keywordmodule
from typing import TypeVar
from modules.shared_log import log_status
# Define the type alias for clarity
StorageType = TypeVar('StorageType', bound=DatabaseManager)

class LeadGenerationTool:
    def __init__(self, input_module: keywordmodule, scraper: ScrapingHandler, storage: StorageType,extractor: LeadExtractor):
        """
        Initializes the tool with dependencies.
        The storage dependency is now explicitly the persistent DatabaseManager.
        """
        self.input_module = input_module
        self.scraper = scraper
        self.storage = storage 
        self.extractor = extractor
        log_status("🔧 LeadGenerationTool initialized.")

    def process_keyword(self, keyword: str, max_seed_urls: int = 20, max_retries: int = 2) -> list[Lead]:
        """
        Processes a single keyword: scrapes, extracts leads, and stores them.
        Retries on timeout/network errors instead of crashing the entire thread.
        Returns the list of newly extracted Leads (objects).
        """
        for attempt in range(max_retries + 1):
            try:
                # 1. Scrape the content -> Use the passed parameter for flexibility
                log_status(f"🔍 Starting search and scraping for seed URLs for '{keyword}'... (attempt {attempt + 1}/{max_retries + 1})")
                clean_urls = self.scraper.scrape_keyword(keyword, max_results=max_seed_urls)

                if not clean_urls:
                    log_status(f"🛑 Skipping keyword '{keyword}' due to failed scrape (no seed URLs found).")
                    return []

                # 2. Extract results using the integrated self.extractor
                log_status(f"🧩 Starting intelligent crawling and extraction from {len(clean_urls)} seed URLs...")

                # Call the extractor using the clean URLs from the scraper (Correct Logic)
                extracted_leads = self.extractor.intelligent_scraper(clean_urls)
                
                valid_leads = [lead for lead in extracted_leads if lead is not None]
                
                # 3. Store the extracted leads using the DatabaseManager
                if valid_leads:
                    count = self.storage.add_all_leads(valid_leads) 
                    log_status(f"✅ Successfully extracted and stored {count} leads for '{keyword}'.")
                else:
                    log_status(f"⚠️ No leads extracted for '{keyword}'.")
                    
                return valid_leads # Return the data collected
                
            except Exception as e:
                if attempt < max_retries:
                    log_status(f"⚠️ Timeout/Error on attempt {attempt + 1}: {str(e)[:100]}... Retrying...")
                else:
                    log_status(f"⚠️ Skipping keyword '{keyword}' after {max_retries + 1} attempts. Last error: {str(e)[:100]}")
                    return []
        
        return []


    # def run(self) -> None:
    #     """
    #     Main execution flow of the lead generation process.
    #     """
    #     conolse_log("\n--- Starting Lead Generation Process...")
        
    #     # 1. Get Keywords
    #     keywords = self.input_module.get_clean_keywords() 
        
    #     if not keywords:
    #         conolse_log("🛑 No keywords found to process. Exiting.")
    #         return
            
    #     conolse_log(f"📝 Found {len(keywords)} keywords to process.")
        
    #     # Optional: Clear old data before starting a new run (Good for testing)
    #     self.storage.clear_storage()
        
    #     # 2. Process each keyword
    #     for keyword in keywords:
    #         self.process_keyword(keyword.strip()) 
        
    #     # 3. Finalization
    #     # Use DatabaseManager's method to get the final count
    #     final_leads_count = len(self.storage.get_all_leads())
    #     conolse_log(f"\n✅ Lead Generation Process Complete! Total leads stored: {final_leads_count}")

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
    
#     # Pass dependencies to the constructor
#     lead_tool = LeadGenerationTool(
#         input_module=input_module, 
#         scraper=scraper, 
#         storage=storage
#     )
    
#     # Run the lead generation process
#     lead_tool.run(extractor_instance=extractor)
    
#     # Fetch and conolse_log results from the Database Manager
#     storage_leads = storage.get_all_leads()
#     conolse_log("\n--- Final Results from Database ---")
#     for lead in storage_leads:
#         # Leads retrieved are ORM objects, so use .to_dict() defined in the ORM model
#         conolse_log(lead.to_dict()) 
#     conolse_log("-----------------------------------")