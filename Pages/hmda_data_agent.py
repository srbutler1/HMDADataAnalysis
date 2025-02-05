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
        self.base_url = "https://ffiec.cfpb.gov/v2/data-browser-api/view"
        self.years_available = list(range(2018, 2024))  # HMDA data from 2018 onwards
        
    def fetch_hmda_data(self, year: int, state_code: str = None, variables: List[str] = None):
        """
        Fetch HMDA data for a specific year and optionally filter by state
        
        Args:
            year: The year to fetch data for (2018 onwards)
            state_code: Optional two-letter state code
            variables: List of HMDA variables to include
        """
        if year not in self.years_available:
            raise ValueError(f"Data only available for years: {self.years_available}")
            
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
            
        params = {
            "years": year,
            "variables": variables
        }
        
        if state_code:
            params["state_code"] = state_code
            
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            
            # Convert response to DataFrame
            df = pd.read_csv(StringIO(response.text))
            
            # Save the data
            filename = f"hmda_data_{year}"
            if state_code:
                filename += f"_{state_code}"
            filename += ".csv"
            
            filepath = os.path.join("uploads", filename)
            df.to_csv(filepath, index=False)
            
            # Update data dictionary
            self._update_data_dictionary(filename, year, state_code, variables)
            
            return filepath
            
        except requests.RequestException as e:
            st.error(f"Error fetching HMDA data: {str(e)}")
            return None
            
    def _update_data_dictionary(self, filename: str, year: int, state_code: str = None, variables: List[str] = None):
        """Update the data dictionary with information about the HMDA dataset"""
        try:
            # Load existing dictionary
            if os.path.exists('data_dictionary.json'):
                with open('data_dictionary.json', 'r') as f:
                    data_dict = json.load(f)
            else:
                data_dict = {}
                
            # Create description
            description = f"HMDA (Home Mortgage Disclosure Act) data for {year}"
            if state_code:
                description += f" in {state_code}"
                
            data_dict[filename] = {
                "description": description,
                "coverage": f"Year: {year}" + (f", State: {state_code}" if state_code else ""),
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
