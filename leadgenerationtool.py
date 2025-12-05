from modules.scrapinghandler import ScrapingHandler
from modules.Lead import Lead
from modules.leadExtractor import LeadExtractor
from modules.Temperorystorage import TemporaryStorage
from modules.keywordmodule import keywordmodule
class LeadGenerationTool:
    # 💥 FIX 1: Change to DOUBLE underscores: __init__
    def __init__(self, input_module: keywordmodule, scraper: ScrapingHandler, storage: TemporaryStorage):
        """
        Initializes the tool with dependencies.
        """
        self.input_module = input_module
        self.scraper = scraper
        self.storage = storage
        print("🔧 LeadGenerationTool initialized.")

    def process_keyword(self, keyword: str, extractor_instance: 'LeadExtractor') -> None:
        """
        Processes a single keyword: scrapes, extracts leads, and stores them.
        (Removed 'source_url' as it's not strictly necessary here and was not used)
        """
        # 1. Scrape the content -> Should return a list of clean URLs
        # 💥 FIX 3A: The output from scrape_keyword is likely a list of URLs
        clean_urls = self.scraper.scrape_keyword(keyword, max_results=20)

        if not clean_urls:
            print(f"🛑 Skipping keyword '{keyword}' due to failed scrape.")
            return

        # 2. Extract results
        print(f"🧩 Processing and storing leads for '{keyword}'...")
        
        # 💥 FIX 3B: Call the extractor's main function with the URLs
        # This assumes your LeadExtractor has a method like extract_leads_from_urls()
        final_leads = extractor_instance.extract_lead_info(clean_urls)
        
        # 3. Store the results
        for lead in final_leads:
            self.storage.add_lead(lead)
        
        print(f"✅ Stored {len(final_leads)} leads for keyword '{keyword}'.")


    def run(self, extractor_instance: 'LeadExtractor') -> None:
        """
        The main execution method.
        """
        print("\n🚀 Starting Lead Generation Process...")
        
        # 1. Get Keywords
        keywords = self.input_module.get_clean_keywords() # Assumes this method exists
        
        if not keywords:
            print("🛑 No keywords found to process. Exiting.")
            return
            
        print(f"📝 Found {len(keywords)} keywords to process.")
        
        # 2. Process each keyword
        for keyword in keywords:
            self.process_keyword(keyword, extractor_instance) # Pass only extractor
        
        # 3. Finalization
        final_leads_count = len(self.storage.get_all_leads())
        print(f"\n✅ Lead Generation Process Complete! Total leads stored: {final_leads_count}")

if __name__ == "__main__":
    # Initialize dependencies
    input_module = keywordmodule()
    scraper = ScrapingHandler()
    storage = TemporaryStorage()
    extractor = LeadExtractor()
    
    # Get user input and set the keywords list
    search_keyword=input("Enter your keywords separated by commas: ")
    input_module.keywords=search_keyword.split(",") # Assuming keywordmodule stores keywords here
    
    # 💥 FIX 2: Pass dependencies to the correctly named constructor
    lead_tool = LeadGenerationTool(
        input_module=input_module, 
        scraper=scraper, 
        storage=storage
    )
    
    # Run the lead generation process
    lead_tool.run(extractor_instance=extractor)
    storage_leads = storage.get_all_leads()
    for lead in storage_leads:
        print(lead.to_dict())

