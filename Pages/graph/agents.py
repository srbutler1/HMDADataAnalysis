from autogen import AssistantAgent, UserProxyAgent, config_list_from_json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import uuid
import os
from typing import List, Dict, Any
from Pages.data_models import InputData

def create_agents(config_list=None, seed=42):
    """Create a team of agents for data analysis"""
    # Use provided config or create default
    if config_list is None:
        config_list = [{
            "model": "gpt-4-1106-preview",
            "api_key": os.getenv("OPENAI_API_KEY")
        }]
    """Create a team of agents for data analysis"""
    
    # Data Analysis Planner - Plans the analysis steps
    planner = AssistantAgent(
        name="planner",
        system_message="""You are a data analysis planner. Your role is to:
1. Break down data analysis tasks into clear, logical steps
2. Consider what visualizations or statistical analyses would be most appropriate
3. Ensure all necessary data validation and preprocessing is planned
4. Pass each step to the executor agent

Always start by planning to check available columns using tools.get_columns('hmda').
Remember that all data is at the state level, so use counties or derived_msa-md for area analysis.

Format your instructions clearly with step numbers and detailed explanations.""",
        description="Plans data analysis steps and strategies",
        llm_config={"config_list": config_list, "seed": seed},
        max_consecutive_auto_reply=3
    )
    
    # Code Executor - Implements the planned steps
    executor = AssistantAgent(
        name="executor",
        system_message="""You are a Python code executor for data analysis. Your role is to:
1. Implement the steps provided by the planner
2. Use the correct tools and functions for each task
3. Handle errors and edge cases appropriately
4. Return results and visualizations

Available functions:
- tools.get_columns('hmda')
- tools.create_scatter_plot('hmda', x_col, y_col, title=None)
- tools.create_line_plot('hmda', x_col, y_col, title=None)
- tools.create_bar_plot('hmda', x_col, y_col, title=None, group_by=None)
- tools.create_histogram('hmda', column, bins=30, title=None)
- tools.create_box_plot('hmda', column, title=None, group_by=None)
- tools.calculate_summary_stats('hmda', columns=None, group_by=None)
- tools.calculate_correlation('hmda', col1, col2)
- tools.create_correlation_matrix('hmda', columns=None)

Always use 'hmda' as the dataset name in all function calls.""",
        description="Executes Python code for data analysis tasks",
        llm_config={"config_list": config_list, "seed": seed},
        max_consecutive_auto_reply=3
    )
    
    # Results Analyzer - Analyzes and explains results
    analyzer = AssistantAgent(
        name="analyzer",
        system_message="""You are a data analysis results analyzer. Your role is to:
1. Interpret visualization outputs and statistical results
2. Identify key patterns, trends, and insights
3. Explain findings in clear, non-technical language
4. Suggest potential follow-up analyses

Focus on providing actionable insights and clear explanations of what the data shows.""",
        description="Analyzes and explains data analysis results",
        llm_config={"config_list": config_list, "seed": seed},
        max_consecutive_auto_reply=3
    )
    
    # User Proxy - Manages the workflow and tool execution
    user_proxy = UserProxyAgent(
        name="user_proxy",
        system_message="""You are a workflow manager for data analysis. Your role is to:
1. Initialize the analysis tools with the provided dataset
2. Route requests between the planner, executor, and analyzer agents
3. Handle file operations and maintain the working environment
4. Ensure proper error handling and logging""",
        code_execution_config={
            "work_dir": "images/plotly_figures",
            "use_docker": False
        },
        human_input_mode="NEVER",
        max_consecutive_auto_reply=3,
        is_termination_msg=lambda x: "TERMINATE" in x.get("content", ""),
        description="Manages the data analysis workflow"
    )
    
    return planner, executor, analyzer, user_proxy

class DataAnalysisTools:
    """Tools for data analysis, made available to the agents"""
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
        """Calculate summary statistics"""
        if data_var not in self.dataframes:
            raise ValueError(f"Dataset {data_var} not found")
            
        df = self.dataframes[data_var]
        if columns is None:
            columns = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
        
        if group_by:
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

    def create_correlation_matrix(self, data_var: str, columns: List[str] = None) -> dict:
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
            fig.write_html(filepath)
            print(f"[Tools] Created visualization: {filename}")
            return {
                'figure': fig,
                'filename': filename
            }
        except Exception as e:
            print(f"[Tools] Error saving figure: {str(e)}")
            raise
