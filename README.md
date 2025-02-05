# HMDA Data Analysis Dashboard

A Streamlit-based dashboard for analyzing Home Mortgage Disclosure Act (HMDA) data with integrated visualization capabilities.

## Credits

This project builds upon the data analysis agent created by [saoudrizwan](https://github.com/saoudrizwan). The original visualization capabilities have been extended to include HMDA data integration while maintaining the core analysis functionality.

## Features

- **HMDA Data Integration**: Fetch and analyze HMDA data directly from the CFPB API
  - Filter by year (2018 onwards)
  - Filter by state
  - Select specific variables
- **Data Visualization**: Create interactive visualizations using Plotly
  - Scatter plots
  - Line plots
  - Bar charts
  - Histograms
  - Box plots
  - Correlation matrices
- **Statistical Analysis**: Calculate and view
  - Summary statistics
  - Correlations between variables
  - Custom analyses through the chat interface

## Setup

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```
3. Create a `.env` file with your OpenAI API key:
```
OPENAI_API_KEY=your_key_here
```

## Usage

1. Run the Streamlit app:
```bash
streamlit run data_analysis_streamlit_app.py
```

2. Use the HMDA Data tab to:
   - Fetch HMDA data for specific years and states
   - View and manage downloaded datasets

3. Use the Visualization Agent tab to:
   - Analyze the data through natural language queries
   - Create custom visualizations
   - Get statistical insights

## HMDA Data Variables

Common HMDA variables available:
- action_taken: The action taken on the application
- loan_type: The type of loan
- loan_purpose: The purpose of the loan
- loan_amount: The amount of the loan
- property_value: The value of the property
- income: The applicant's income
- state_code: The state where the property is located

## Contributing

Feel free to submit issues and enhancement requests!

## License

MIT License
