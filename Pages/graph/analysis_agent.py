import pandas as pd
import numpy as np
import json
import os
from typing import Dict, Any, Optional
from datetime import datetime

class AnalysisAgent:
    """A flexible agent for analyzing data and outputs"""
    
    def __init__(self):
        self.log_prefix = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [AnalysisAgent]"
    
    def log(self, msg: str, level: str = "INFO"):
        """Log a message with timestamp"""
        print(f"{self.log_prefix} [{level}] {msg}")

    def analyze(self, data: Any, data_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze any type of data and return structured results
        
        Args:
            data: The data to analyze (DataFrame, Series, dict, etc.)
            data_type: Optional hint about the data type
            
        Returns:
            Dict containing analysis results with keys:
            - success: bool indicating if analysis succeeded
            - data_type: str describing the type of data analyzed
            - metrics: Dict of numerical metrics
            - insights: List of text insights
            - error: Optional error message if analysis failed
        """
        self.log(f"Starting analysis of {type(data)}")
        
        try:
            # Determine data type if not provided
            if data_type is None:
                data_type = self._determine_data_type(data)
            self.log(f"Data type determined: {data_type}")
            
            # Initialize results
            results = {
                "success": True,
                "data_type": data_type,
                "metrics": {},
                "insights": [],
                "error": None
            }
            
            # Analyze based on type
            if data_type == "visualization":
                self._analyze_visualization(data, results)
            elif data_type == "error":
                self._analyze_error(data, results)
            elif data_type == "dataframe":
                self._analyze_dataframe(data, results)
            elif data_type == "series":
                self._analyze_series(data, results)
            elif data_type == "dict":
                self._analyze_dict(data, results)
            elif data_type == "list":
                self._analyze_list(data, results)
            else:
                self._analyze_generic(data, results)
            
            self.log("Analysis completed successfully")
            return results
            
        except Exception as e:
            self.log(f"Analysis failed: {str(e)}", "ERROR")
            return {
                "success": False,
                "data_type": "unknown",
                "metrics": {},
                "insights": [],
                "error": str(e)
            }

    def _determine_data_type(self, data: Any) -> str:
        """Determine the type of data for analysis"""
        if isinstance(data, str):
            if data.endswith('.pickle') or (isinstance(data, str) and 'Visualization created successfully' in data):
                return "visualization"
            elif data.startswith('ValueError'):
                return "error"
            elif data.startswith('[') and data.endswith(']'):
                # Try to parse as list
                try:
                    eval(data)
                    return "list"
                except:
                    pass
            elif data.startswith('{') and data.endswith('}'):
                # Try to parse as dict
                try:
                    json.loads(data)
                    return "dict"
                except:
                    pass
        elif isinstance(data, pd.DataFrame):
            return "dataframe"
        elif isinstance(data, pd.Series):
            return "series"
        elif isinstance(data, dict):
            return "dict"
        elif isinstance(data, (list, tuple)):
            return "list"
        return "generic"

    def _analyze_error(self, error_msg: str, results: Dict[str, Any]):
        """Analyze an error message"""
        # Extract the actual error message from ValueError
        if error_msg.startswith('ValueError("'):
            error_msg = error_msg[11:-2]  # Remove ValueError(" and ")
        
        results["metrics"].update({
            "error_type": "ValueError" if error_msg.startswith('Value') else "Unknown",
            "message_length": len(error_msg)
        })
        
        # For column-related errors, try to extract column information
        if "Expected one of" in error_msg:
            try:
                columns_str = error_msg.split("Expected one of ")[1].split(" but received")[0]
                available_columns = eval(columns_str)
                results["metrics"]["available_columns"] = available_columns
                results["insights"].extend([
                    "Error: Invalid column name specified",
                    f"Available columns: {len(available_columns)}",
                    "Use one of the available columns listed in the metrics"
                ])
            except:
                results["insights"].append(f"Error: {error_msg}")
        else:
            results["insights"].append(f"Error: {error_msg}")

    def _analyze_visualization(self, data: Dict[str, Any], results: Dict[str, Any]):
        """Analyze a visualization"""
        self.log("Analyzing visualization")
        
        try:
            if not isinstance(data, dict) or 'figure' not in data:
                results["insights"].extend([
                    "Visualization created successfully",
                    "The plot is available in HTML format",
                    f"You can view the interactive plot at: images/plotly_figures/{data.get('filename', '')}"
                ])
                return
                
            fig = data['figure']
            # Get plot type and title
            plot_type = fig.data[0].type if fig.data else "unknown"
            title = fig.layout.title.text if hasattr(fig.layout, 'title') else "Untitled"
            
            results["metrics"].update({
                "plot_type": plot_type,
                "title": title
            })
            
            # Analyze based on plot type
            if plot_type == "box":
                if hasattr(fig.data[0], 'y'):
                    y_values = pd.Series(fig.data[0].y)
                    results["metrics"].update({
                        "median": y_values.median(),
                        "q1": y_values.quantile(0.25),
                        "q3": y_values.quantile(0.75),
                        "min": y_values.min(),
                        "max": y_values.max()
                    })
                    results["insights"].extend([
                        f"Plot Type: Box Plot - {title}",
                        f"Distribution Analysis:",
                        f"- Median: {results['metrics']['median']:,.2f}",
                        f"- Q1 (25th percentile): {results['metrics']['q1']:,.2f}",
                        f"- Q3 (75th percentile): {results['metrics']['q3']:,.2f}",
                        f"- Range: {results['metrics']['min']:,.2f} to {results['metrics']['max']:,.2f}"
                    ])
            elif plot_type == "bar":
                if hasattr(fig.data[0], 'y'):
                    y_values = pd.Series(fig.data[0].y)
                    x_values = pd.Series(fig.data[0].x)
                    results["metrics"].update({
                        "mean": y_values.mean(),
                        "max_value": y_values.max(),
                        "min_value": y_values.min(),
                        "top_categories": dict(sorted(zip(x_values, y_values), key=lambda x: x[1], reverse=True)[:5])
                    })
                    results["insights"].extend([
                        f"Plot Type: Bar Chart - {title}",
                        f"Analysis:",
                        f"- Average Value: {results['metrics']['mean']:,.2f}",
                        f"- Highest Value: {results['metrics']['max_value']:,.2f}",
                        f"- Lowest Value: {results['metrics']['min_value']:,.2f}",
                        "Top 5 Categories:"
                    ])
                    for cat, val in results["metrics"]["top_categories"].items():
                        results["insights"].append(f"  • {cat}: {val:,.2f}")
            else:
                # Generic analysis for other plot types
                results["insights"].extend([
                    f"Plot Type: {plot_type}",
                    f"Title: {title}",
                    "The visualization has been created successfully and can be viewed in the browser"
                ])
            
            # Add HTML file location
            if 'filename' in data:
                results["insights"].append(f"\nView the interactive plot at: images/plotly_figures/{data['filename']}")
            
        except Exception as e:
            self.log(f"Error analyzing visualization: {str(e)}", "ERROR")
            results["error"] = str(e)

    def _analyze_dataframe(self, df: pd.DataFrame, results: Dict[str, Any]):
        """Analyze a pandas DataFrame"""
        results["metrics"].update({
            "shape": df.shape,
            "columns": list(df.columns),
            "dtypes": df.dtypes.to_dict(),
            "missing": df.isnull().sum().to_dict()
        })
        
        # Analyze numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            results["metrics"]["numeric_summary"] = df[numeric_cols].describe().to_dict()
            
        results["insights"].extend([
            f"DataFrame with {df.shape[0]} rows and {df.shape[1]} columns",
            f"Numeric columns: {len(numeric_cols)}",
            f"Missing values: {df.isnull().sum().sum()}"
        ])

    def _analyze_series(self, series: pd.Series, results: Dict[str, Any]):
        """Analyze a pandas Series"""
        results["metrics"].update({
            "length": len(series),
            "dtype": str(series.dtype),
            "missing": series.isnull().sum()
        })
        
        if np.issubdtype(series.dtype, np.number):
            results["metrics"].update({
                "mean": series.mean(),
                "median": series.median(),
                "std": series.std(),
                "min": series.min(),
                "max": series.max()
            })
            
        results["insights"].extend([
            f"Series of type {results['metrics']['dtype']} with {results['metrics']['length']} elements",
            f"Missing values: {results['metrics']['missing']}"
        ])

    def _analyze_dict(self, data: Dict, results: Dict[str, Any]):
        """Analyze a dictionary"""
        results["metrics"].update({
            "keys": list(data.keys()),
            "length": len(data),
            "value_types": {k: type(v).__name__ for k, v in data.items()}
        })
        
        results["insights"].extend([
            f"Dictionary with {len(data)} keys",
            f"Key types: {set(type(k).__name__ for k in data.keys())}"
        ])

    def _analyze_list(self, data: Any, results: Dict[str, Any]):
        """Analyze a list or list-like object"""
        if isinstance(data, str):
            try:
                data = eval(data)
            except:
                self._analyze_generic(data, results)
                return
                
        results["metrics"].update({
            "length": len(data),
            "element_types": list(set(type(x).__name__ for x in data))
        })
        
        results["insights"].extend([
            f"List with {len(data)} elements",
            f"Element types: {', '.join(results['metrics']['element_types'])}"
        ])
        
        # If all elements are strings or numbers, add some basic stats
        if all(isinstance(x, (str, int, float)) for x in data):
            if all(isinstance(x, (int, float)) for x in data):
                results["metrics"].update({
                    "min": min(data),
                    "max": max(data),
                    "mean": sum(data) / len(data)
                })
                results["insights"].append(
                    f"Numeric range: {results['metrics']['min']} to {results['metrics']['max']}"
                )
            else:
                results["metrics"]["unique_values"] = len(set(data))
                results["insights"].append(
                    f"Unique values: {results['metrics']['unique_values']}"
                )

    def _analyze_generic(self, data: Any, results: Dict[str, Any]):
        """Analyze any other type of data"""
        str_data = str(data)
        results["metrics"].update({
            "type": type(data).__name__,
            "string_length": len(str_data),
            "dir_attributes": len(dir(data)),
            "lines": len(str_data.split('\n'))
        })
        
        results["insights"].extend([
            f"Generic data of type {type(data).__name__}",
            f"Content length: {results['metrics']['string_length']} characters",
            f"Number of lines: {results['metrics']['lines']}"
        ])
