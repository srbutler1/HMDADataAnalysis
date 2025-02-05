import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import uuid
import pickle
import os
from typing import List, Dict, Any
from Pages.data_models import InputData

class DataAnalysisTools:
    def __init__(self, input_data: List[InputData]):
        self.dataframes = {}
        for data in input_data:
            try:
                df = pd.read_csv(data.data_path)
                self.dataframes[data.variable_name] = df
            except Exception as e:
                print(f"Error loading {data.data_path}: {str(e)}")

    def create_scatter_plot(self, data_var: str, x_col: str, y_col: str, title: str = None) -> str:
        """Create a scatter plot using plotly"""
        if data_var not in self.dataframes:
            raise ValueError(f"Dataset {data_var} not found")
            
        df = self.dataframes[data_var]
        fig = px.scatter(df, x=x_col, y=y_col, title=title)
        return self._save_figure(fig)

    def create_line_plot(self, data_var: str, x_col: str, y_col: str, title: str = None) -> str:
        """Create a line plot using plotly"""
        if data_var not in self.dataframes:
            raise ValueError(f"Dataset {data_var} not found")
            
        df = self.dataframes[data_var]
        fig = px.line(df, x=x_col, y=y_col, title=title)
        return self._save_figure(fig)

    def create_bar_plot(self, data_var: str, x_col: str, y_col: str, title: str = None) -> str:
        """Create a bar plot using plotly"""
        if data_var not in self.dataframes:
            raise ValueError(f"Dataset {data_var} not found")
            
        df = self.dataframes[data_var]
        fig = px.bar(df, x=x_col, y=y_col, title=title)
        return self._save_figure(fig)

    def create_histogram(self, data_var: str, column: str, bins: int = 30, title: str = None) -> str:
        """Create a histogram using plotly"""
        if data_var not in self.dataframes:
            raise ValueError(f"Dataset {data_var} not found")
            
        df = self.dataframes[data_var]
        fig = px.histogram(df, x=column, nbins=bins, title=title)
        return self._save_figure(fig)

    def create_box_plot(self, data_var: str, column: str, title: str = None) -> str:
        """Create a box plot using plotly"""
        if data_var not in self.dataframes:
            raise ValueError(f"Dataset {data_var} not found")
            
        df = self.dataframes[data_var]
        fig = px.box(df, y=column, title=title)
        return self._save_figure(fig)

    def calculate_summary_stats(self, data_var: str, columns: List[str] = None) -> Dict[str, Any]:
        """Calculate summary statistics for specified columns"""
        if data_var not in self.dataframes:
            raise ValueError(f"Dataset {data_var} not found")
            
        df = self.dataframes[data_var]
        if columns is None:
            columns = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
            
        return df[columns].describe().to_dict()

    def calculate_correlation(self, data_var: str, col1: str, col2: str) -> float:
        """Calculate correlation between two columns"""
        if data_var not in self.dataframes:
            raise ValueError(f"Dataset {data_var} not found")
            
        df = self.dataframes[data_var]
        return df[col1].corr(df[col2])

    def create_correlation_matrix(self, data_var: str, columns: List[str] = None) -> str:
        """Create a correlation matrix heatmap"""
        if data_var not in self.dataframes:
            raise ValueError(f"Dataset {data_var} not found")
            
        df = self.dataframes[data_var]
        if columns is None:
            columns = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
            
        corr_matrix = df[columns].corr()
        fig = go.Figure(data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns,
            y=corr_matrix.columns,
            colorscale='RdBu'
        ))
        fig.update_layout(title='Correlation Matrix')
        return self._save_figure(fig)

    def _save_figure(self, fig) -> str:
        """Save plotly figure and return the filename"""
        if not os.path.exists("images/plotly_figures/pickle"):
            os.makedirs("images/plotly_figures/pickle")
            
        filename = f"{uuid.uuid4()}.pickle"
        filepath = os.path.join("images/plotly_figures/pickle", filename)
        
        with open(filepath, 'wb') as f:
            pickle.dump(fig, f)
            
        return filename
