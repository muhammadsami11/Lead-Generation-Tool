import streamlit as st
import pandas as pd
import time
import queue
import threading
import random
import os
from typing import List, TypeVar
# NOTE: Ensure all these modules are available in your environment
from modules.scrapinghandler import ScrapingHandler
from modules.leadExtractor import LeadExtractor
from modules.database_manager import DatabaseManager 
from modules.keywordmodule import keywordmodule
from leadgenerationtool import LeadGenerationTool 
from modules.LeadValidator import LeadValidator
from modules.shared_log import LOG_QUEUE, log_status
import yaml
import streamlit_authenticator as stauth
from yaml import SafeLoader
with open('credentials.yaml') as file: 
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# Handle authentication
try:
    authenticator.login(location='main')
except Exception as e:
    st.error(e)

if st.session_state.get('authentication_status'):
    # --- GLOBAL LOGGING & THREAD SETUP (shared via modules.shared_log) ---

        def update_frontend_log():
            """Reads messages from the shared queue and updates session state."""
            log_messages = []
            while not LOG_QUEUE.empty():
                try:
                    log_messages.append(LOG_QUEUE.get_nowait())
                except Exception:
                    break

            if log_messages:
                if 'process_log' not in st.session_state or st.session_state['process_log'] is None:
                    st.session_state['process_log'] = []
                st.session_state['process_log'].extend(log_messages)

        # --- INITIALIZATION FUNCTIONS ---

        @st.cache_resource
        def initialize_backend():
            """Initializes and caches the expensive backend components."""
            try:
                # Instantiate dependencies
                input_module = keywordmodule()
                scraper = ScrapingHandler()
                storage = DatabaseManager()
                extractor = LeadExtractor()
                validator = LeadValidator()
                
                # Initialize the main tool
                # CRITICAL FIX 1: Pass the extractor instance to the constructor
                lead_tool = LeadGenerationTool(
                    input_module=input_module, 
                    scraper=scraper, 
                    storage=storage,
                    validator=validator
                )
                log_status("✅ Backend components initialized and cached.")
                return lead_tool, storage, extractor
            except Exception as e:
                log_status(f"❌ FATAL ERROR during backend initialization: {e}")
                print(f"FATAL ERROR during backend initialization: {e}")
                return None, None

        def run_extraction_process_in_thread(keywords_list, lead_tool, db_storage, extractor, max_visits, max_depth):
            """
            Wrapper function to run the process in a separate thread.
            This function orchestrates the keyword processing loop.
            """
            try:
                log_status("--- STARTING INTELLIGENT SCRAPE ---")
                
                # 1. Set Global Limits on Extractor before starting search
                if hasattr(extractor, 'MAX_VISITS'):
                    extractor.MAX_VISITS = max_visits
                if hasattr(extractor, 'MAX_DEPTH'):
                    extractor.MAX_DEPTH = max_depth
                
                all_final_leads_data = []
                
                for keyword in keywords_list:
                    clean_keyword = keyword.strip()
                    if not clean_keyword:
                        continue
                        
                    log_status(f"🌐 Checking database for keyword: '{clean_keyword}'")
                    
                    # --- DATABASE CHECK FIRST ---
                    # Use the permanent database for cache lookup
                    cached_leads = db_storage.get_leads_by_keyword(clean_keyword)
                    
                    if cached_leads and len(cached_leads) > 0:
                        log_status(f"✅ Found {len(cached_leads)} cached leads for '{clean_keyword}' in database.")
                        log_status(f"📋 Using cached data - skip Google search for '{clean_keyword}'")
                        all_final_leads_data.extend(cached_leads)
                        continue
                    else:
                        log_status(f"📭 No cached leads found for '{clean_keyword}' in database.")
                        
                    # --- SEARCH GOOGLE SINCE NO CACHED DATA ---
                    log_status(f"🌐 Searching Google for leads related to '{clean_keyword}'...")
                    
                    try:
                        # CRITICAL FIX 2: Call the orchestrator method (process_keyword) 
                        # which handles the scrape, extraction, and internal storage.
                        lead_tool.process_keyword(
                            keyword=clean_keyword,
                            extractor_instance=extractor
                        )
                        log_status(f"✅ Google search and lead extraction completed for '{clean_keyword}'")
                        log_status(f"💾 Leads saved to database for future searches")
                    except Exception as e:
                        log_status(f"❌ Error during Google search for '{clean_keyword}': {str(e)}")
                        continue
                
                # --- FINAL RESULTS: Fetch all leads from database ---
                log_status("\n📊 Fetching extracted leads from database...")
                all_leads_from_db = db_storage.get_all_leads()
                
                if all_leads_from_db:
                    # Convert Lead ORM objects to dicts for Streamlit display
                    all_final_leads_data = []
                    for lead in all_leads_from_db:
                        try:
                            if hasattr(lead, 'to_dict'):
                                all_final_leads_data.append(lead.to_dict())
                            elif isinstance(lead, dict):
                                all_final_leads_data.append(lead)
                            else:
                                log_status(f"⚠️ Unknown lead type: {type(lead)}")
                        except Exception as e:
                            log_status(f"⚠️ Failed to convert lead: {e}")
                    
                    log_status(f"✅ Retrieved {len(all_final_leads_data)} total leads from database")
                    log_status("💡 Note: Results include all previously extracted leads")
                else:
                    all_final_leads_data = []
                    log_status("⚠️ No leads found in database after processing")
                
                st.session_state['results'] = all_final_leads_data
                st.session_state['execution_status'] = "Success"

            except Exception as e:
                log_status(f"\n❌ FATAL THREAD ERROR: {e}")
                st.session_state['execution_status'] = "Error"
            finally:
                st.session_state['scraping_thread'] = None


        # --- INITIALIZE GLOBAL VARIABLES ---
        lead_tool, db_storage, extractor = initialize_backend()

        # Initialize Session State
        if 'results' not in st.session_state:
            st.session_state['results'] = None
        if 'execution_status' not in st.session_state:
            st.session_state['execution_status'] = "Ready"
            
        # FIX 1: Set the default MAX_VISITS to 3 for quick testing
        if 'max_visits' not in st.session_state:
            st.session_state['max_visits'] = 3 
        if 'max_depth' not in st.session_state:
            st.session_state['max_depth'] = 2
        if 'process_log' not in st.session_state:
            st.session_state['process_log'] = []
        if 'scraping_thread' not in st.session_state:
            st.session_state['scraping_thread'] = None


        # --- STREAMLIT UI DEFINITION ---

        st.set_page_config(
            page_title="AI Lead Generation Tool",
            page_icon="🕵️‍♂️",
            layout="wide"
        )

        st.title("🕵️‍♂️ AI Lead Generation Tool")
        st.markdown("A highly focused scraper utilizing **A* Search (Intelligent Navigation)** and **Game Theory (Anti-Block)** defenses.")

        # --- SIDEBAR (SETTINGS) ---
        with st.sidebar:
            authenticator.logout(location='main')
            st.header("⚙️ Search Configuration")
            
            # Ensure `is_running` is always a boolean. Use getattr to safely call is_alive()
            _thread_obj = st.session_state.get('scraping_thread')
            is_running = bool(_thread_obj and getattr(_thread_obj, 'is_alive', lambda: False)())
            
            st.info("Status: " + st.session_state['execution_status'])
            
            # 1. Input for Max Visits Limit (FIXED FOR TYPE SAFETY)
            # Ensure value is reset to an integer if Streamlit/user interaction sets it to None
            if st.session_state.get('max_visits') is None:
                st.session_state['max_visits'] = 3
                
            # Guard against None values stored in session state
            safe_max_visits = st.session_state.get('max_visits') or 3
            
            max_visits = st.number_input(
                "Max Links to Visit (Per Site)", 
                min_value=3, 
                max_value=50, 
                value=int(safe_max_visits), # Guaranteed not to be None
                step=1, 
                key='max_visits',
                disabled=is_running
            )
            st.caption("A* will stop searching after this many links, regardless of depth.")
            
            # 2. Input for Max Depth Limit (FIXED FOR TYPE SAFETY)
            # Ensure value is reset to an integer if Streamlit/user interaction sets it to None
            if st.session_state.get('max_depth') is None:
                st.session_state['max_depth'] = 2

            safe_max_depth = st.session_state.get('max_depth') or 2

            max_depth = st.slider(
                "Max Search Depth (g(n) limit)", 
                1, 
                5, 
                value=int(safe_max_depth), # Guaranteed not to be None
                key='max_depth',
                disabled=is_running
            )
            st.caption("How deep the search should go (1 is homepage only).")
            
            deep_search = st.checkbox("Enable Deep Search (A*)", value=True, help="Disabling A* results in a simpler BFS/DFS.", disabled=is_running)


        # --- MAIN CONTENT AREA (TABS) ---
        tab_input, tab_results = st.tabs(["Input", "Results"])

        with tab_input:
            st.subheader("1. Enter Search Keywords")
            
            keywords_input = st.text_area(
                "🔎 Keywords (comma-separated):",
                placeholder="e.g., Skincare brands, SaaS companies in London, Gyms in Dubai",
                height=100,
                disabled=is_running
            )

            if st.button("🚀 Start Extraction Process", type="primary", use_container_width=True, disabled=is_running):
                
                if not lead_tool:
                    st.error("FATAL ERROR: Backend failed to initialize. Cannot run process.")
                elif not keywords_input:
                    st.error("❌ Please enter some keywords to begin.")
                else:
                    keyword_list = [k.strip() for k in keywords_input.split(",") if k.strip()]
                    
                    # Clear old state
                    st.session_state['results'] = None 
                    st.session_state['process_log'] = []
                    st.session_state['execution_status'] = "Processing..."
                    
                    # --- START NEW THREAD FOR BACKEND WORK ---
                    thread_args = (keyword_list, lead_tool, db_storage, extractor, max_visits, max_depth)
                    
                    st.session_state['scraping_thread'] = threading.Thread(
                        target=run_extraction_process_in_thread, 
                        args=thread_args
                    )
                    st.session_state['scraping_thread'].start()
                    
                    st.rerun() # Rerun immediately to show the status update


        # --- RESULTS AND LIVE LOG DISPLAY ---
        with tab_results:
            st.subheader("2. Extracted Leads Dashboard")

            # 1. Update and Show Live Log
            update_frontend_log()
            
            # Display live log regardless of status
            st.subheader("Live Backend Log")
            st.code("\n".join(st.session_state['process_log']) if st.session_state['process_log'] else "[Waiting for logs...]", language='log')
            
            # Check if still processing
            _thread_obj = st.session_state.get('scraping_thread')
            _is_thread_alive = bool(_thread_obj and getattr(_thread_obj, 'is_alive', lambda: False)())
            
            if st.session_state['execution_status'] == "Processing..." and _is_thread_alive:
                st.info("🔄 The intelligent scraper is running in the background. Refresh to see updates.")
                # Allow user to manually refresh instead of forced rerun
                if st.button("🔄 Refresh Results", use_container_width=True):
                    st.rerun()
            
            elif st.session_state['results']:
                # 2. Display Final Results
                try:
                    results_data = st.session_state['results']
                    
                    # Ensure all items are dicts, not ORM objects
                    if results_data and isinstance(results_data[0], dict):
                        df = pd.DataFrame(results_data)
                    else:
                        # Try to convert ORM objects to dicts
                        converted_results = []
                        for item in results_data:
                            if hasattr(item, 'to_dict'):
                                converted_results.append(item.to_dict())
                            elif isinstance(item, dict):
                                converted_results.append(item)
                            else:
                                log_status(f"⚠️ Skipping non-dict/non-ORM item: {type(item)}")
                        df = pd.DataFrame(converted_results) if converted_results else pd.DataFrame()
                    
                    if df.empty:
                        st.warning("⚠️ No leads data to display (empty DataFrame).")
                    else:
                        # Clean up the column names for the frontend
                        df.columns = [col.replace('_', ' ').title() for col in df.columns]
                        
                        # Display key metrics
                        col_count, col_email = st.columns(2)
                        col_count.metric("Total Leads Stored", len(df))
                        col_email.metric("Leads with Email", df['Email'].notna().sum() if 'Email' in df.columns else 0)
                        
                        st.markdown("### Detailed Results Table")
                        st.dataframe(df, use_container_width=True)

                        # Download Button
                        csv = df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="💾 Download All Leads (CSV)",
                            data=csv,
                            file_name=f'leads_export_{time.strftime("%Y%m%d_%H%M%S")}.csv',
                            mime='text/csv',
                        )
                except Exception as e:
                    st.error(f"❌ Error displaying results: {e}")
                    log_status(f"❌ Frontend display error: {e}")

            else:
                st.info("No successful results to display yet. Start a new search using the 'Start New Extraction' tab.")

else:
    if st.session_state.get('authentication_status') is False:
        st.error('Username/password is incorrect')
    elif st.session_state.get('authentication_status') is None:
        st.warning('Please enter your username and password')