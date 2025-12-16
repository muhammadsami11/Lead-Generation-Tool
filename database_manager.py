import os
from typing import List
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.orm import sessionmaker, declarative_base
from modules.Lead import Lead # Import the Lead data model

# Define the base class for declarative class definitions
Base = declarative_base()

# --- ORM Model Definition ---
class LeadORM(Base):
    """
    SQLAlchemy ORM model for the 'leads' table.
    Maps the Lead object attributes to database columns.
    """
    __tablename__ = 'leads'

    # Primary key
    id = Column(Integer, primary_key=True) 
    
    # Key fields to store. website_url is set to unique to prevent duplicates.
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    website_url = Column(String(512), unique=True, nullable=False)
    scraped_at = Column(String(50), nullable=True)

    def to_dict(self):
        """Converts the ORM object to a dictionary for external use."""
        return {
            'name': self.name,
            'email': self.email,
            'website_url': self.website_url,
            'scraped_at': self.scraped_at,
        }

    def __repr__(self):
        return f"<LeadORM(name='{self.name}', url='{self.website_url}')>"


# --- Database Manager Class ---
class DatabaseManager:
    """
    Handles all interactions with the SQLite database using SQLAlchemy.
    It manages connections, table creation, and CRUD operations.
    """
    DB_FILE_NAME = 'leads_database.db'
    
    def __init__(self, db_file: str = None):
        """
        Initializes the database connection and ensures the table exists.
        """
        if db_file is None:
            # This line ensures the database file is created inside the 'modules' directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            db_file = os.path.join(current_dir, self.DB_FILE_NAME)
        
        print(f"💾 Initializing Database at: {db_file}")

        # SQLite connection string
        self.engine = create_engine(f'sqlite:///{db_file}')
        
        # Create tables (checks LeadORM and creates the 'leads' table if not exists)
        Base.metadata.create_all(self.engine) 
        
        # Create a configured Session class
        self.Session = sessionmaker(bind=self.engine)

    def add_all_leads(self, leads: List[Lead]) -> int:
        """
        Adds a list of Lead objects to the database, skipping duplicates.
        """
        session = self.Session()
        new_leads_added = 0
        try:
            orm_objects = []
            for lead in leads:
                # Check for existing lead by website_url
                exists = session.query(LeadORM).filter_by(website_url=lead.source_url).first()
                
                if not exists:
                    # Create a new ORM object from the Lead model
                    orm_lead = LeadORM(
                        name=lead.title, 
                        email=getattr(lead, 'email', None),
                        website_url=lead.source_url,
                        scraped_at=lead.scraped_at
                    )
                    orm_objects.append(orm_lead)
                    new_leads_added += 1
            
            # Use bulk addition for efficiency
            if orm_objects:
                session.add_all(orm_objects)
                session.commit()
            
            return new_leads_added

        except Exception as e:
            session.rollback()
            print(f"❌ Database Error during bulk insertion: {e}")
            return 0
        finally:
            session.close()

    def get_all_leads(self) -> List[LeadORM]:
        """
        Retrieves all stored leads from the database.
        """
        session = self.Session()
        try:
            # Query all records
            leads = session.query(LeadORM).all()
            return leads
        except Exception as e:
            print(f"❌ Database Error during retrieval: {e}")
            return []
        finally:
            session.close()

    def clear_storage(self) -> None:
        """
        Deletes all records from the 'leads' table.
        """
        session = self.Session()
        try:
            deleted_count = session.query(LeadORM).delete()
            session.commit()
            print(f"[{self.__class__.__name__}] Storage reset: Cleared {deleted_count} leads from database.")
        except Exception as e:
            session.rollback()
            print(f"❌ Database Error during clear operation: {e}")
        finally:
            session.close()