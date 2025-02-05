import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import uuid
import os
from typing import List, Dict, Any
from Pages.data_models import InputData

class DataAnalysisTools:
    def __init__(self, input_data: List[InputData]):
        self.dataframes = {'hmda': None}  # Initialize with 'hmda' key
        
        if not input_data:
            raise ValueError("No input data provided. Please upload a dataset first.")
            
        data = input_data[0]  # Take only the first dataset
        if not data.data_path or not os.path.exists(data.data_path):
            raise ValueError(f"Invalid data path: {data.data_path}")
            
        try:
            df = pd.read_csv(data.data_path, low_memory=False)
            if df.empty:
                raise ValueError(f"Dataset is empty")
            # Always use 'hmda' as the dataset name
            self.dataframes['hmda'] = df
            print(f"\n[Tools] Loaded dataset with {len(df)} rows and {len(df.columns)} columns")
            print("[Tools] Available columns:")
            for col in df.columns:
                print(f"  - {col}")
        except Exception as e:
            raise ValueError(f"Error loading {data.data_path}: {str(e)}")
                
    def get_columns(self, data_var: str) -> List[str]:
        """Get list of available columns in the dataset"""
        if data_var not in self.dataframes:
            raise ValueError(f"Dataset {data_var} not found")
        return list(self.dataframes[data_var].columns)

    def create_scatter_plot(self, data_var: str, x_col: str, y_col: str, title: str = None) -> dict:
        """Create a scatter plot"""
        if data_var not in self.dataframes:
            raise ValueError(f"Dataset {data_var} not found")
        
        df = self.dataframes[data_var]
        df[y_col] = pd.to_numeric(df[y_col], errors='coerce')
        
        fig = px.scatter(df, x=x_col, y=y_col, title=title)
        fig.update_layout(showlegend=True, xaxis_tickangle=-45)
        return self._save_figure(fig)

    def create_line_plot(self, data_var: str, x_col: str, y_col: str, title: str = None) -> dict:
        """Create a line plot"""
        if data_var not in self.dataframes:
            raise ValueError(f"Dataset {data_var} not found")
        
        df = self.dataframes[data_var]
        df[y_col] = pd.to_numeric(df[y_col], errors='coerce')
        
        fig = px.line(df, x=x_col, y=y_col, title=title)
        fig.update_layout(showlegend=True, xaxis_tickangle=-45)
        return self._save_figure(fig)

    def create_bar_plot(self, data_var: str, x_col: str, y_col: str, title: str = None, group_by: str = None) -> dict:
        """Create a bar plot"""
        if data_var not in self.dataframes:
            raise ValueError(f"Dataset {data_var} not found")
        
        df = self.dataframes[data_var]
        df[y_col] = pd.to_numeric(df[y_col], errors='coerce')
        
        if group_by:
            grouped_df = df.groupby([x_col, group_by])[y_col].mean().reset_index()
            fig = px.bar(grouped_df, x=x_col, y=y_col, color=group_by, title=title, barmode='group')
        else:
            grouped_df = df.groupby(x_col)[y_col].mean().reset_index()
            fig = px.bar(grouped_df, x=x_col, y=y_col, title=title)
        
        fig.update_layout(showlegend=True, xaxis_tickangle=-45)
        return self._save_figure(fig)

    def create_histogram(self, data_var: str, column: str, bins: int = 30, title: str = None) -> dict:
        """Create a histogram"""
        if data_var not in self.dataframes:
            raise ValueError(f"Dataset {data_var} not found")
        
        df = self.dataframes[data_var]
        df[column] = pd.to_numeric(df[column], errors='coerce')
        
        fig = px.histogram(df, x=column, nbins=bins, title=title)
        fig.update_layout(showlegend=True, xaxis_tickangle=-45)
        return self._save_figure(fig)

    def create_box_plot(self, data_var: str, column: str, title: str = None, group_by: str = None) -> dict:
        """Create a box plot"""
        if data_var not in self.dataframes:
            raise ValueError(f"Dataset {data_var} not found")
        
        df = self.dataframes[data_var]
        df[column] = pd.to_numeric(df[column], errors='coerce')
        
        if group_by:
            fig = px.box(df, x=group_by, y=column, title=title)
        else:
            fig = px.box(df, y=column, title=title)
        
        fig.update_layout(showlegend=True, xaxis_tickangle=-45)
        return self._save_figure(fig)

    def calculate_summary_stats(self, data_var: str, columns: List[str] = None, group_by: str = None) -> Dict[str, Any]:
        """Calculate summary statistics for specified columns, optionally grouped by a column"""
        if data_var not in self.dataframes:
            raise ValueError(f"Dataset {data_var} not found")
            
        df = self.dataframes[data_var]
        if columns is None:
            columns = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
        
        if group_by:
            # Calculate summary stats for each group
            stats = {}
            for group_val in df[group_by].unique():
                group_df = df[df[group_by] == group_val]
                stats[str(group_val)] = group_df[columns].describe().to_dict()
            return stats
        else:
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

    def _save_figure(self, fig) -> dict:
        """Save plotly figure as HTML and return the figure and filename"""
        if not os.path.exists("images/plotly_figures"):
            os.makedirs("images/plotly_figures")
            
        filename = f"{uuid.uuid4()}.html"
        filepath = os.path.join("images/plotly_figures", filename)
        
        try:
            # Save HTML version
            fig.write_html(filepath)
            print(f"[Tools] Created visualization: {filename}")
            
            # Return both the figure object and filename
            return {
                'figure': fig,
                'filename': filename
            }
        except Exception as e:
            print(f"[Tools] Error saving figure: {str(e)}")
            raise
