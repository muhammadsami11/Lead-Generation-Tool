from modules.database_manager import DatabaseManager 
from modules.keywordmodule import keywordmodule
from typing import TypeVar
import os
import sys
import pandas as pd

# Add the project root to the path so modules can be imported
# This assumes the test file is run from the project root (leadGenerationTool directory)
# sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the necessary manager class
from modules.database_manager import DatabaseManager

def test_database_retrieval():
    """
    Initializes the DatabaseManager and prints all stored leads.
    """
    print("--- Starting Database Retrieval Test ---")

    # 1. Initialize the DatabaseManager
    # It will automatically find 'leads_database.db' inside the 'modules' directory
    try:
        db_manager = DatabaseManager()
    except Exception as e:
        print(f"❌ ERROR: Failed to initialize DatabaseManager. Check SQLAlchemy installation and imports. Error: {e}")
        return

    # 2. Retrieve all leads
    print("\nAttempting to retrieve all leads...")
    retrieved_orm_leads = db_manager.get_all_leads()
    
    if not retrieved_orm_leads:
        print("✅ Retrieval complete. Database is empty (0 leads found).")
        return
        
    # 3. Process and display data
    
    # Convert ORM objects (LeadORM) to simple dictionaries
    final_leads_data = [lead.to_dict() for lead in retrieved_orm_leads]

    print(f"\n✅ Retrieval successful! Total leads found: {len(final_leads_data)}\n")
    
    # Optional: Display nicely using pandas DataFrame
    try:
        leads_df = pd.DataFrame(final_leads_data)
        print("--- Detailed Lead Data (DataFrame View) ---")
        # Print the DataFrame without index for cleaner output
        print(leads_df.to_string(index=False)) 
    except ImportError:
        # Fallback if pandas is not installed
        print("--- Detailed Lead Data (Dictionary View) ---")
        for lead in final_leads_data:
            print(lead)

    print("\n--- Test Complete ---")


if __name__ == "__main__":
    # Ensure pandas is installed for the nice table view
    try:
        import pandas as pd
    except ImportError:
        print("Note: pandas not found. Install with 'pip install pandas' for cleaner table output.")
        
    test_database_retrieval()