from modules.scrapinghandler import ScrapingHandler
from modules.Lead import Lead
from modules.leadExtractor import LeadExtractor
# 💥 CRITICAL FIX: Replace TemporaryStorage with the permanent DatabaseManager
from modules.database_manager import DatabaseManager 
from modules.keywordmodule import keywordmodule
from modules.LeadValidator import LeadValidator
from typing import TypeVar

# Define the type alias for clarity
StorageType = TypeVar('StorageType', bound=DatabaseManager)

class LeadGenerationTool:
    def __init__(self, input_module: keywordmodule, scraper: ScrapingHandler, storage: StorageType, validator: LeadValidator):
        """
        Initializes the tool with dependencies.
        The storage dependency is now explicitly the persistent DatabaseManager.
        """
        self.input_module = input_module
        self.scraper = scraper
        self.storage = storage
        self.validator = validator
        print("🔧 LeadGenerationTool initialized.")

    def process_keyword(self, keyword: str, extractor_instance: 'LeadExtractor') -> None:
        """
        Processes a single keyword: scrapes, extracts leads, and stores them.
        """
        # 1. Scrape the content -> Should return a list of clean URLs
        clean_urls = self.scraper.scrape_keyword(keyword, max_results=20)

        if not clean_urls:
            print(f"🛑 Skipping keyword '{keyword}' due to failed scrape (no URLs found).")
            return

        # 2. Extract results
        print(f"🧩 Processing and storing leads for '{keyword}'...")
        
        extracted_leads = extractor_instance.extract_lead_info(clean_urls)
        
        # 2.5. Validate the extracted leads
        if extracted_leads:
            print(f"🔍 Validating {len(extracted_leads)} leads...")
            for lead in extracted_leads:
                self.validator.validate_lead(lead)
        
        # 3. Store the extracted leads using the DatabaseManager
        if extracted_leads:
            # 💥 CRITICAL FIX: Use the efficient add_all_leads method from DatabaseManager
            count = self.storage.add_all_leads(extracted_leads, keyword=keyword) 
            print(f"✅ Successfully extracted, validated, and stored {count} leads for '{keyword}'.")
        else:
            print(f"⚠️ No leads extracted for '{keyword}'.")


    def run(self, extractor_instance: 'LeadExtractor') -> None:
        """
        Main execution flow of the lead generation process.
        """
        print("\n--- Starting Lead Generation Process...")
        
        # 1. Get Keywords
        keywords = self.input_module.get_clean_keywords() 
        
        if not keywords:
            print("🛑 No keywords found to process. Exiting.")
            return
            
        print(f"📝 Found {len(keywords)} keywords to process.")
        
        # Optional: Clear old data before starting a new run (Good for testing)
        self.storage.clear_storage()
        
        # 2. Process each keyword
        for keyword in keywords:
            self.process_keyword(keyword, extractor_instance) 
        
        # 3. Finalization
        # Use DatabaseManager's method to get the final count
        final_leads_count = len(self.storage.get_all_leads())
        print(f"\n✅ Lead Generation Process Complete! Total leads stored: {final_leads_count}")

import subprocess
import sys
import os

if __name__ == "__main__":
    # Launch the Streamlit frontend
    print("🚀 Launching Lead Generation Tool Frontend...")
    try:
        # Get the directory of the current script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        frontend_path = os.path.join(script_dir, 'frontend.py')
        
        # Run streamlit
        subprocess.run([
            sys.executable, '-m', 'streamlit', 'run', frontend_path
        ], cwd=script_dir)
    except Exception as e:
        print(f"❌ Failed to launch frontend: {e}")
        print("Make sure Streamlit is installed and the frontend.py file exists.")