import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

os.environ["STREAMLIT_SERVER_MAX_UPLOAD_SIZE"] = "2000"
import streamlit as st

# Set Streamlit to wide mode
st.set_page_config(layout="wide", page_title="HMDA Data Analysis", page_icon="📊")

data_visualisation_page = st.Page(
    "./Pages/python_visualisation_agent.py", title="Data Visualisation", icon="📈"
)

hmda_data_page = st.Page(
    "./Pages/hmda_data_agent.py", title="HMDA Data", icon="🏠"
)

pg = st.navigation(
    {
        "HMDA Data": [hmda_data_page],
        "Visualisation Agent": [data_visualisation_page]
    }
)

pg.run()
