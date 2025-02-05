import os
from dotenv import load_dotenv
import pandas as pd
import json
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

import streamlit as st

# Set Streamlit to wide mode
st.set_page_config(layout="wide", page_title="HMDA Data Analysis", page_icon="📊")

# Create necessary directories if they don't exist
for dir_path in ["uploads", "images/plotly_figures/pickle"]:
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

# Initialize data dictionary if it doesn't exist
if not os.path.exists('data_dictionary.json'):
    with open('data_dictionary.json', 'w') as f:
        f.write('{}')

st.title("HMDA Data Analysis Dashboard")

tab1, tab2 = st.tabs(["HMDA Data", "Analysis Assistant"])

with tab1:
    from Pages.hmda_data_agent import HMDADataAgent
    
    hmda_agent = HMDADataAgent()
    
    st.header("Fetch HMDA Data")
    
    # Year and State Selection
    col1, col2 = st.columns(2)
    with col1:
        selected_year = st.selectbox("Select Year", hmda_agent.years_available)
    with col2:
        state_code = st.text_input("State Code (e.g., TX)", max_chars=2)
    
    if st.button("Fetch HMDA Data"):
        if not state_code:
            st.error("Please enter a state code")
        else:
            with st.spinner("Fetching data..."):
                filepath = hmda_agent.fetch_hmda_data(selected_year, state_code)
                if filepath:
                    st.success(f"Data saved to {filepath}")
            
    # Display existing datasets
    st.header("Available Datasets")
    
    # Load data dictionary
    with open('data_dictionary.json', 'r') as f:
        data_dictionary = json.load(f)
    
    available_files = [f for f in os.listdir("uploads") if f.endswith('.csv')]
    
    if available_files:
        for file in available_files:
            with st.expander(file):
                try:
                    df = pd.read_csv(os.path.join("uploads", file), low_memory=False)
                    st.write("Preview:")
                    st.dataframe(df.head())
                    
                    if file in data_dictionary:
                        st.write("Dataset Information:")
                        st.json(data_dictionary[file])
                        
                    st.write(f"Total Records: {len(df):,}")
                    st.write(f"Columns: {', '.join(df.columns)}")
                except Exception as e:
                    st.error(f"Error loading {file}: {str(e)}")
    else:
        st.info("No datasets available. Use the form above to fetch HMDA data.")

with tab2:
    from Pages.data_models import InputData
    from Pages.graph.autogen_backend import AutoGenBackend
    import os
    
    st.header("HMDA Research Assistant")
    
    # Get list of available CSV files
    available_files = [f for f in os.listdir("uploads") if f.endswith('.csv')]
    
    if available_files:
        # File selection
        selected_files = st.multiselect(
            "Select datasets to analyze",
            available_files,
            key="selected_files"
        )
        
        if selected_files:
            # Show info about using 'hmda' as dataset name
            st.info("Use 'hmda' as the dataset name in all your queries. For example:\n- What's the average loan amount?\n- Show me loan amounts by county\n- Compare property values across different areas")
            
            # Initialize AutoGen backend if not exists or if initialization failed
            if ('autogen_backend' not in st.session_state or 
                not getattr(st.session_state.autogen_backend, '_is_initialized', False)):
                
                print("[App] Initializing AutoGen backend...")
                st.session_state.autogen_backend = AutoGenBackend()
                config_list = [{"model": "gpt-4-1106-preview", "api_key": os.getenv("OPENAI_API_KEY")}]
                
                init_success = st.session_state.autogen_backend.initialize_agents(config_list)
                if not init_success:
                    st.error("Failed to initialize AI agents. Please check your configuration and try again.")
                    if 'autogen_backend' in st.session_state:
                        del st.session_state.autogen_backend
                    st.stop()
                else:
                    print("[App] Successfully initialized AutoGen backend")
                
            # Create two columns: main chat and agent log
            chat_col, log_col = st.columns([1, 1])

            with chat_col:
                st.markdown("### Main Chat")
                chat_container = st.container(height=500)

            with log_col:
                st.markdown("### Agent Conversation Log")
                log_container = st.container(height=500)

            def process_chat(user_query):
                if not user_query:
                    return
                
                if selected_files:
                    file = selected_files[0]
                    input_data = [InputData(
                        variable_name='hmda',
                        data_path=os.path.abspath(os.path.join("uploads", file)),
                        data_description=data_dictionary.get(file, {}).get('description', '')
                    )]
                    
                    # Process query
                    with st.spinner("Processing query..."):
                        result = st.session_state.autogen_backend.process_query(user_query, input_data)
                    
                    if not result['success']:
                        st.error(f"Error: {result['error']}")
                        return
                    
                    # Store results in session state
                    st.session_state.chat_messages = result['messages']
                    st.session_state.raw_messages = result.get('raw_messages', [])
                    st.rerun()

            # Display chat history
            with chat_container:
                if 'chat_messages' in st.session_state:
                    for msg in st.session_state.chat_messages:
                        role = msg.get('role', 'assistant')
                        content = msg.get('content', '')
                        
                        if role == 'user':
                            st.chat_message('user').markdown(content)
                        else:
                            with st.chat_message('assistant'):
                                st.markdown(content)

            # Display agent log
            with log_container:
                if 'raw_messages' in st.session_state:
                    for msg in st.session_state.raw_messages:
                        role = msg.get('role', 'unknown')
                        content = msg.get('content', '')
                        
                        if role == 'planner':
                            st.markdown(f"📋 **Planner:**\n{content}")
                        elif role == 'executor':
                            st.markdown(f"⚙️ **Executor:**\n{content}")
                        elif role == 'analyzer':
                            st.markdown(f"📊 **Analyzer:**\n{content}")
                        else:
                            st.markdown(f"🤖 **{role.title()}:**\n{content}")
                        st.divider()

            # Chat input
            user_query = st.chat_input(
                placeholder="Ask questions about the HMDA data...",
                key="chat_input"  # Changed from user_input to chat_input
            )
            
            if user_query:
                process_chat(user_query)
        else:
            st.info("Please select datasets to analyze.")
    else:
        st.info("No data available. Please fetch some HMDA data in the Data Management tab first.")
