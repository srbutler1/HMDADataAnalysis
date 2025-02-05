HMDA_FILTERS = {
    "construction_methods": {
        "description": "Construction method of the property",
        "options": {
            "1": "Site-Built",
            "2": "Manufactured"
        }
    },
    "dwelling_categories": {
        "description": "Type and construction of dwelling",
        "options": {
            "Single Family (1-4 Units):Site-Built": "Single Family (1-4 Units) Site-Built",
            "Multifamily:Site-Built": "Multifamily Site-Built",
            "Single Family (1-4 Units):Manufactured": "Single Family (1-4 Units) Manufactured",
            "Multifamily:Manufactured": "Multifamily Manufactured"
        }
    },
    "ethnicities": {
        "description": "Ethnicity of applicant(s)",
        "options": [
            "Hispanic or Latino",
            "Not Hispanic or Latino",
            "Joint",
            "Ethnicity Not Available",
            "Free Form Text Only"
        ]
    },
    "lien_statuses": {
        "description": "Lien status of the loan",
        "options": {
            "1": "First Lien",
            "2": "Subordinate Lien"
        }
    },
    "loan_products": {
        "description": "Type and lien status of loan",
        "options": [
            "Conventional:First Lien",
            "FHA:First Lien",
            "VA:First Lien",
            "FSA/RHS:First Lien",
            "Conventional:Subordinate Lien",
            "FHA:Subordinate Lien",
            "VA:Subordinate Lien",
            "FSA/RHS:Subordinate Lien"
        ]
    },
    "loan_purposes": {
        "description": "Purpose of the loan",
        "options": {
            "1": "Home purchase",
            "2": "Home improvement",
            "31": "Refinancing",
            "32": "Cash-out refinancing",
            "4": "Other purpose",
            "5": "Not applicable"
        }
    },
    "loan_types": {
        "description": "Type of loan",
        "options": {
            "1": "Conventional",
            "2": "FHA",
            "3": "VA",
            "4": "FSA/RHS"
        }
    },
    "races": {
        "description": "Race of applicant(s)",
        "options": [
            "Asian",
            "Native Hawaiian or Other Pacific Islander",
            "Free Form Text Only",
            "Race Not Available",
            "American Indian or Alaska Native",
            "Black or African American",
            "2 or more minority races",
            "White",
            "Joint"
        ]
    },
    "sexes": {
        "description": "Sex of applicant(s)",
        "options": [
            "Male",
            "Female",
            "Joint",
            "Sex Not Available"
        ]
    },
    "total_units": {
        "description": "Total units in the property",
        "options": [
            "1",
            "2",
            "3",
            "4",
            "5-24",
            "25-49",
            "50-99",
            "100-149",
            ">149"
        ]
    }
}

def get_filter_description(filter_name):
    """Get the description of a filter"""
    return HMDA_FILTERS.get(filter_name, {}).get("description", "")

def get_filter_options(filter_name):
    """Get the available options for a filter"""
    return HMDA_FILTERS.get(filter_name, {}).get("options", [])

def get_filters_for_analysis(analysis_type):
    """Get relevant filters based on type of analysis requested"""
    analysis_mappings = {
        "lending_patterns": ["loan_products", "loan_purposes", "loan_types"],
        "demographics": ["ethnicities", "races", "sexes"],
        "property_analysis": ["construction_methods", "dwelling_categories", "total_units"],
        "lien_analysis": ["lien_statuses", "loan_products"],
    }
    return analysis_mappings.get(analysis_type, [])
