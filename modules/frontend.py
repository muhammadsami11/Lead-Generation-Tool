import streamlit as st
import pandas as pd
import time
import queue
import threading
import random
import os
import yaml
from yaml import SafeLoader
from pathlib import Path
import streamlit_authenticator as stauth
from typing import List, TypeVar

# --- MODULE IMPORTS WITH ERROR HANDLING ---
try:
    from .scrapinghandler import ScrapingHandler
    from .leadExtractor import LeadExtractor
    from .database_manager import DatabaseManager 
    from .keywordmodule import keywordmodule
    from .leadgenerationtool import LeadGenerationTool 
    from .LeadValidator import LeadValidator
    from .shared_log import log_status, LOG_QUEUE
    from .login import authenticate_user, render_simple_login, logout as simple_logout
except (ImportError, ValueError):
    import sys
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    from modules.scrapinghandler import ScrapingHandler
    from modules.leadExtractor import LeadExtractor
    from modules.database_manager import DatabaseManager 
    from modules.keywordmodule import keywordmodule
    from modules.leadgenerationtool import LeadGenerationTool 
    from modules.LeadValidator import LeadValidator
    from modules.shared_log import log_status, LOG_QUEUE
    from modules.login import authenticate_user, render_simple_login, logout as simple_logout

# --- CONFIGURATION & AUTHENTICATION SETUP ---
ROOT_DIR = Path(__file__).resolve().parents[1]
with open(ROOT_DIR / 'credentials.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)


if 'authenticator' not in st.session_state:
    st.session_state['authenticator'] = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days']
    )

authenticator = st.session_state['authenticator']

# 3. Use the stored instance



# Import the simple login helpers (standalone/simple form) to integrate with frontend


# 1. Initialize variables to avoid "not defined" errors
authentication_status = None
name = None
username = None

# 2. Render Login Form using the integrated simple login module
# Prefer the standard widget if available, otherwise fall back to the simple form.
try:
    result = None
    try:
        # Try the widget-style authenticator first (renders cookies, etc.)
        result = authenticate_user("Login", "sidebar")
    except Exception:
        result = None

    if result and any(v is not None for v in result):
        name, authentication_status, username = result
    else:
        # Fallback: render the simple login form (works even if the widget fails)
        name, authentication_status, username = render_simple_login("Login", "sidebar")
except Exception as e:
    st.error(f"Authentication Error: {e}")
    # Final fallback
    name, authentication_status, username = render_simple_login("Login", "sidebar")

# --- MAIN APP LOGIC (Only runs if authenticated) ---
if authentication_status:
    # Sidebar Logout & Welcome
    st.sidebar.header("Successfully Logged In ✅")
    # Logout widget may raise if the authenticator doesn't think the user is logged in.
    if st.sidebar.button("Logout"):
        simple_logout()
        try:
            authenticator.logout('Logout', 'sidebar')
        except Exception:
            # Ignore logout errors (fallback is the Reset simple login button)
            pass
        st.rerun()
    st.sidebar.success(f"Welcome, {name}")

    # --- GLOBAL LOGGING & THREAD SETUP ---
    def update_frontend_log():
        log_messages = []
        while not LOG_QUEUE.empty():
            try:
                log_messages.append(LOG_QUEUE.get_nowait())
            except:
                break
        if log_messages:
            if 'process_log' not in st.session_state:
                st.session_state['process_log'] = []
            st.session_state['process_log'].extend(log_messages)

    # --- INITIALIZATION FUNCTIONS ---
    @st.cache_resource
    def initialize_backend():
        try:
            input_module = keywordmodule()
            scraper = ScrapingHandler()
            storage = DatabaseManager()
            extractor = LeadExtractor()
            validator = LeadValidator()
            extractor = LeadExtractor()

            lead_tool = LeadGenerationTool(
                input_module=input_module, 
                scraper=scraper, 
                storage=storage,
                extractor=extractor,
                validator=validator
            )
            return lead_tool, storage
        except Exception as e:
            st.error(f"Backend Init Error: {e}")
            return None, None

    def run_extraction_process_in_thread(keywords_list, lead_tool, db_storage, max_visits, max_depth,max_seed_urls=10):
        try:
            log_status("--- STARTING INTELLIGENT SCRAPE ---")
            if hasattr(lead_tool.extractor, 'MAX_VISITS'):
                lead_tool.extractor.MAX_VISITS = max_visits
            if hasattr(lead_tool.extractor, 'MAX_DEPTH'):
                lead_tool.extractor.MAX_DEPTH = max_depth
            if hasattr(lead_tool.scraper, 'MAX_RESULTS'):
                lead_tool.scraper.MAX_RESULTS = max_seed_urls
            for keyword in keywords_list:
                clean_keyword = keyword.strip()
                if not clean_keyword: continue
                
                log_status(f"🌐 Checking DB for: '{clean_keyword}'")
                cached_leads = db_storage.get_leads_by_keyword(clean_keyword)
                
                if cached_leads:
                    log_status(f"✅ Found {len(cached_leads)} leads in DB. Skipping scrape.")
                    continue
                
                log_status(f"🔍 Starting A* search for '{clean_keyword}'...")
                lead_tool.process_keyword(keyword=clean_keyword, extractor_instance=LeadExtractor())

            all_leads_from_db = db_storage.get_all_leads()
            st.session_state['results'] = [l.to_dict() if hasattr(l, 'to_dict') else l for l in all_leads_from_db]
            st.session_state['execution_status'] = "Success"
        except Exception as e:
            log_status(f"❌ Thread Error: {e}")
            st.session_state['execution_status'] = "Error"
        finally:
            st.session_state['scraping_thread'] = None

    # --- UI STATE & APP RENDERING ---
    lead_tool, db_storage = initialize_backend()

    if 'execution_status' not in st.session_state:
        st.session_state.update({'results': None, 'execution_status': "Ready", 'process_log': [], 'scraping_thread': None})

    st.set_page_config(page_title="AI Lead Generation Tool", page_icon="🕵️‍♂️", layout="wide")
    st.title("🕵️‍♂️ AI Lead Generation Tool")
    
    with st.sidebar:
        st.header("⚙️ Configuration")
        # Allow clearing the simple-login session (for testing and logout parity)
        if st.button("Reset simple login"):
            simple_logout()
            st.experimental_rerun()
        if st.button("🔄 Refresh Data & Logs", use_container_width=True):
            update_frontend_log() # Pull messages from the thread to the UI
            st.rerun() # Force the GUI to redraw
        if st.button("leads from DB", use_container_width=True):
            all_leads = db_storage.get_all_leads()
            for lead in all_leads:
                log_status(f"Lead: {lead.to_dict()}")
            st.rerun()    
        if st.button("Clear All Leads in DB", use_container_width=True):
            db_storage.clear_all_leads()
            log_status("🗑️ Cleared all leads from the database.")
            st.rerun()
           
        _thread = st.session_state.get('scraping_thread')
        is_running = bool(_thread and _thread.is_alive())
        
        st.info(f"Status: {st.session_state['execution_status']}")
        max_v = st.number_input("Max Links", 3, 50, value=3, key='max_visits_ui', disabled=is_running)
        max_d = st.slider("Max Depth", 1, 5, value=2, key='max_depth_ui', disabled=is_running)
        max_seed_urls = st.slider("Max Seed URLs", 5, 50, value=20, key='max_seed_urls_ui', disabled=is_running)

    tab_input, tab_results = st.tabs(["Input", "Results"])

    with tab_input:
        keywords_input = st.text_area("🔎 Keywords (comma-separated):", placeholder="e.g. SaaS London", disabled=is_running)
        if st.button("🚀 Start Extraction", type="primary", disabled=is_running):
            if keywords_input:
                k_list = [k.strip() for k in keywords_input.split(",") if k.strip()]
                st.session_state.update({'results': None, 'process_log': [], 'execution_status': "Processing..."})
                st.session_state['scraping_thread'] = threading.Thread(
                    target=run_extraction_process_in_thread, 
                    args=(k_list, lead_tool, db_storage, max_v, max_d,max_seed_urls)
                )
                st.session_state['scraping_thread'].start()
                st.rerun()

    with tab_results:
        # 1. Always pull logs first to keep the UI in sync
        update_frontend_log() 
        
        st.subheader("🕵️‍♂️ Extraction Activity")
        st.code("\n".join(st.session_state['process_log']) if st.session_state['process_log'] else "[No active extraction]")
        
        # 2. Check current thread status
        _thread = st.session_state.get('scraping_thread')
        is_running = bool(_thread and _thread.is_alive())

        # 3. AUTO-REFRESH: Keep the loop alive ONLY if processing
        if is_running:
            st.info("🔄 Lead Discovery in progress... Database updated live below.")
            time.sleep(2)
            st.rerun() 
        elif st.session_state.get('execution_status') == "Processing...":
            # Thread just finished; do one final sync
            st.session_state['execution_status'] = "Success"
            st.rerun()

        st.markdown("---")

        # 4. PERMANENT DATABASE VIEW & DOWNLOAD
        # We fetch fresh leads from DB so the table and button are ALWAYS visible
        all_leads = db_storage.get_all_leads() 
        
        if all_leads:
            st.subheader(f"📊 Centralized Database")
            
            # Convert DB objects to DataFrame for display
            df = pd.DataFrame([l.to_dict() for l in all_leads]) 
            
            st.metric("Total Stored Leads", len(df))
            st.dataframe(df, use_container_width=True)
            
            # The Download Button - now available even if not searching
            csv_data = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="💾 Download Entire Database (CSV)",
                data=csv_data,
                file_name=f'all_leads_{int(time.time())}.csv',
                mime='text/csv',
                use_container_width=True,
                key="permanent_download_btn"
            )
        else:
            st.warning("Database is empty. Use the 'Input' tab to start finding leads.")
elif authentication_status is False:
    st.error('Username/password is incorrect')
elif authentication_status is None:
    st.warning('Please enter your credentials to access the Lead Generation Tool.')