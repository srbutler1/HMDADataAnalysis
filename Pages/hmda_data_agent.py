import pandas as pd
import requests
from io import StringIO
import streamlit as st
import os
import json
from typing import List
from Pages.data_models import InputData

class HMDADataAgent:
    """Agent for fetching and processing HMDA (Home Mortgage Disclosure Act) data"""
    
    def __init__(self):
        self.base_url = "https://ffiec.cfpb.gov/v2/data-browser-api/view/csv"
        self.years_available = list(range(2018, 2024))  # HMDA data from 2018 to 2023
        
    def fetch_hmda_data(self, year: int, state_code: str, variables: List[str] = None):
        """
        Fetch HMDA data for a specific year and state
        
        Args:
            year: The year to fetch data for (2018 onwards)
            state_code: Two-letter state code (required)
            variables: List of HMDA variables to include
        """
        if year not in self.years_available:
            raise ValueError(f"Data only available for years: {self.years_available}")
            
        if not state_code:
            raise ValueError("State code is required")
            
        if variables is None:
            variables = [
                "action_taken",
                "loan_type",
                "loan_purpose",
                "loan_amount",
                "property_value",
                "income",
                "state_code"
            ]
            
        # Build parameters
        params = []
        
        # Add year
        params.append(("years", str(year)))
        
        # Add state code
        params.append(("states", state_code.upper()))
        
        # Add variables
        for var in variables:
            params.append(("variables", var))
            
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            
            # Convert response to DataFrame with low_memory=False to handle mixed types
            df = pd.read_csv(StringIO(response.text), low_memory=False)
            
            # Save the data
            filename = f"hmda_data_{year}_{state_code.upper()}.csv"
            filepath = os.path.join("uploads", filename)
            df.to_csv(filepath, index=False, encoding='utf-8')
            
            # Update data dictionary
            self._update_data_dictionary(filename, year, state_code, variables)
            
            return filepath
            
        except requests.RequestException as e:
            st.error(f"Error fetching HMDA data: {str(e)}")
            if hasattr(e.response, 'text'):
                st.error(f"Response content: {e.response.text}")
            return None
            
    def _update_data_dictionary(self, filename: str, year: int, state_code: str, variables: List[str] = None):
        """Update the data dictionary with information about the HMDA dataset"""
        try:
            # Load existing dictionary
            if os.path.exists('data_dictionary.json'):
                with open('data_dictionary.json', 'r') as f:
                    data_dict = json.load(f)
            else:
                data_dict = {}
                
            # Create description
            description = f"HMDA (Home Mortgage Disclosure Act) data for {year} in {state_code.upper()}"
                
            data_dict[filename] = {
                "description": description,
                "coverage": f"Year: {year}, State: {state_code.upper()}",
                "features": variables if variables else [],
                "usage": [
                    "Analyze mortgage lending patterns",
                    "Study loan approval rates",
                    "Examine property values and loan amounts",
                    "Investigate potential lending disparities"
                ],
                "linkage": "Can be linked with other HMDA datasets by year and geography"
            }
            
            # Save updated dictionary
            with open('data_dictionary.json', 'w') as f:
                json.dump(data_dict, f, indent=4)
                
        except Exception as e:
            st.error(f"Error updating data dictionary: {str(e)}")
