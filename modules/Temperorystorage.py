from typing import List, Optional, Type
from dataclasses import dataclass, field
from datetime import datetime
import uuid

# --- DEPENDENCY HANDLING (Ensures standalone testing) ---
# We define a Mock Lead class to ensure this module can be tested 
# independently if the data_model file hasn't been written yet.
try:
    # Attempt to import the real Lead class defined by Ashir
    from modules import Lead as LeadModel
except ImportError:
    # Fallback to a mock Lead class structure based on the class diagram
    @dataclass
    class LeadModel:
        name: str = ""
        website_url: str = ""
        source_url: str = ""
        scraped_at: datetime = field(default_factory=datetime.now)
        id: str = field(default_factory=lambda: str(uuid.uuid4()))
        email: Optional[str] = None
# Set the reference type
Lead = LeadModel


class TemporaryStorage:
    """
    Implements the TemporaryStorage class as required for Sprint 1.
    
    Function: Holds all Lead objects in a simple, in-memory Python list 
    until the permanent database integration (Firestore) is ready in Sprint 2.
    """
    
    def __init__(self):
        """
        Initializes the storage by creating an empty Python list (_leads).
        This list is the internal storage container.
        """
        # Internal list corresponding to the ':list<LEAD> leads' attribute
        self._leads = []  # type: List[Lead]
        print(f"[{self.__class__.__name__}] Initialized: In-memory list storage ready.")

    def add_lead(self, lead: Lead):
        """
        Adds a single Lead object to the temporary storage list.
        Corresponds to the '+add_lead(lead)' method.
        
        Args:
            lead (Lead): The Lead object to be added.
        """
        self._leads.append(lead)

    def add_all_leads(self, leads: List[Lead]):
        """
        Efficiently adds a list (batch) of Lead objects to the storage. 
        This is the method the main controller will primarily use.
        
        Args:
            leads (List[Lead]): A list of Lead objects to add.
        """
        if leads:
            self._leads.extend(leads)
            print(f"[{self.__class__.__name__}] Added {len(leads)} leads in batch.")

    def get_all_leads(self) -> List[Lead]:
        """
        Retrieves all currently stored Lead objects.
        Corresponds to the '+get_all_leads(): list<Lead>' method.
        
        Returns:
            List[Lead]: The complete list of leads currently held in memory.
        """
        return self._leads

    def clear_storage(self):
        """
        Empties the temporary storage list, resetting the state.
        Corresponds to the '+Clear_storage()' method.
        """
        count = len(self._leads)
        self._leads = []
        print(f"[{self.__class__.__name__}] Storage reset: Cleared {count} leads.")

# ----------------------------------------------------------------------
# Standalone Test Block (Optional but Recommended for Verification)
# ----------------------------------------------------------------------
# if __name__ == "__main__":
#     print("\n--- Running Standalone Test for TemporaryStorage ---")
    
#     storage = TemporaryStorage()
    
#     # Create mock leads for testing
#     lead_a = Lead(name="Design Studio X", website_url="designx.com")
#     lead_b = Lead(name="Tech Innovators", website_url="tech.net")
    
#     # Test adding a batch
#     batch_leads = [lead_a, lead_b, Lead(name="Marketing Pro", website_url="mpro.io")]
#     storage.add_all_leads(batch_leads)
    
#     # Check retrieval
#     all_data = storage.get_all_leads()
#     print(f"\nTotal Leads Stored: {len(all_data)}")
    
#     # Check clearing
#     storage.clear_storage()
#     print(f"Final Count after Clear: {len(storage.get_all_leads())}")
    