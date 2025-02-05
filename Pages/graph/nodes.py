
from typing import Annotated, Sequence, TypedDict, Union
from datetime import datetime
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from langchain_core.messages import AIMessage, BaseMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from openai import OpenAI
from langchain_experimental.utilities import PythonREPL
from Pages.graph.tools import DataAnalysisTools
from Pages.graph.analysis_agent import AnalysisAgent
import os

# Initialize analysis agent
analysis_agent = AnalysisAgent()

def call_model(state):
    """Process the messages with the LLM"""
    print("\n[Agent] Processing messages with LLM...")
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a helpful data analysis assistant. You can help analyze data and create visualizations using Python.

CRITICAL INSTRUCTIONS:

1. Dataset Access:
   - ALWAYS use 'hmda' as the dataset name in ALL function calls
   - DO NOT try to use the actual filename or any other name
   - The dataset is ALWAYS accessed as 'hmda' regardless of which file was selected

2. Column Names:
   - ALWAYS check available columns first using tools.get_columns('hmda')
   - Use ONLY the exact column names that are returned
   - Common geographical columns: 'derived_msa-md', 'county_code', 'census_tract'
   - Common analysis columns: 'loan_amount', 'property_value', 'income'

Example workflow:
```python
# First, get available columns
columns = tools.get_columns('hmda')
print(columns)  # Review the output to find correct column names

# Then create visualizations using confirmed column names
tools.create_histogram('hmda', 'loan_amount')
tools.create_bar_plot('hmda', 'derived_msa-md', 'property_value')
tools.create_box_plot('hmda', 'loan_amount', group_by='derived_race')
```

Available functions:
tools.get_columns('hmda')  # Always use 'hmda' to get columns
tools.create_scatter_plot('hmda', x_col, y_col, title=None)
tools.create_line_plot('hmda', x_col, y_col, title=None)
tools.create_bar_plot('hmda', x_col, y_col, title=None, group_by=None)
tools.create_histogram('hmda', column, bins=30, title=None)
tools.create_box_plot('hmda', column, title=None, group_by=None)
tools.calculate_summary_stats('hmda', columns=None, group_by=None)
tools.calculate_correlation('hmda', col1, col2)
tools.create_correlation_matrix('hmda', columns=None)

IMPORTANT: DO NOT try to use the actual dataset filename or any other name.
The dataset is ALWAYS accessed as 'hmda' regardless of which file was selected.

For analyzing disparities between groups:
1. Use create_box_plot with group_by to compare distributions
2. Use create_bar_plot with group_by to compare averages
3. Use calculate_summary_stats with group_by to get detailed statistics


IMPORTANT: Always check the available columns first using tools.get_columns() 
before attempting any analysis. This will help you understand what data is available
and prevent errors from using non-existent column names.

IMPORTANT: You must use these functions through the tools object. Do not try to access the data directly. 
For example, DO NOT use pandas operations like df[column] or data.head().
Instead, use the provided functions to analyze and visualize the data.

IMPORTANT: Always use 'hmda' as the dataset name in all functions. This is a persistent variable 
that will always refer to the currently selected dataset. You don't need to worry about the actual 
filename - just use 'hmda' for all operations.
ALL DATA IS ALREADY AT THE STATE LEVEL. IF ASKED TO ANALYZE BY AREA, USE COUNTIES OR ANOTHER LOWER LEVEL LIKE derived_msa-md

Other tools should be displaying the visualisation you produce. 
         
You should:
1. First check if a dataset is available by looking at the [Tools] log messages
2. Use tools.get_columns() to understand what data is available
3. Understand what analysis/visualization is being requested
4. Write Python code using only the available functions and confirmed column names
5. Handle any errors gracefully and provide clear error messages
6. Explain your findings from the analysis

Format your response as:

If you are creating a visualization or performing analysis:
Thought: Your reasoning about what analysis to perform
Code: ```python
# Your code here
```
Analysis: Leave this section empty. The visualization and analysis results will be provided after code execution.

If you are receiving analysis results:
Analysis: Provide a clear interpretation of the analysis results that were just provided. Focus on explaining what the data shows, key patterns, and important insights. Never say you cannot view the results - use the analysis data that was just provided to you."""),
        MessagesPlaceholder(variable_name="messages"),
    ])
    
    llm = ChatOpenAI(
        model="gpt-4-1106-preview",
        temperature=0
    )
    
    response = llm.invoke(prompt.invoke({"messages": state["messages"]}))
    print(f"\n[Agent] LLM Response:\n{response.content}")
    state["messages"].append(response)
    
    return state

def route_to_tools(state):
    """Route to tools if code execution is needed"""
    print("\n[Router] Determining next step...")
    last_message = state["messages"][-1]
    
    # If there's Python code to execute, route to tools
    if "```python" in last_message.content:
        print("[Router] Python code detected, routing to tools")
        return "tools"
    
    # If this is a tools execution result, route back to model for analysis
    if "Visualization Analysis:" in last_message.content or "Analysis Results:" in last_message.content:
        print("[Router] Analysis results detected, routing to model")
        return "model"
        
    # If no code to execute or analyze, end the conversation
    print("[Router] No code or analysis needed, ending conversation")
    return "end"

def call_tools(state):
    """Execute the Python code and capture outputs"""
    print("\n[Tools] Executing Python code...")
    last_message = state["messages"][-1]
    
    # Extract code and thought
    try:
        code_block = last_message.content.split("```python")[1].split("```")[0].strip()
        thought = last_message.content.split("Thought:")[1].split("Code:")[0].strip()
    except IndexError:
        error_msg = "Invalid message format. Expected 'Thought:' followed by 'Code:' with Python code block."
        state["messages"].append(AIMessage(content=f"Code execution failed. {error_msg}"))
        return state
    
    # Initialize tools and namespace
    try:
        tools = DataAnalysisTools(state["input_data"])
        namespace = {
            "tools": tools,
            "state": state,
            "pd": pd,  # Add pandas for data manipulation
            "px": px,  # Add plotly express for additional plotting
            "go": go   # Add plotly graph objects
        }
    except Exception as e:
        error_msg = f"Failed to initialize tools: {str(e)}"
        state["messages"].append(AIMessage(content=f"Code execution failed. {error_msg}"))
        return state
    
    # Execute the code with enhanced output capture
    repl = PythonREPL(_globals=namespace)
    try:
        print(f"\n[Tools] Running code:\n{code_block}")
        
        # Split code into statements but keep them together
        statements = code_block.strip().split('\n')
        
        # Execute all statements except the last one
        for stmt in statements[:-1]:
            if stmt.strip() and not stmt.strip().startswith('#'):
                repl.run(stmt)
        
        # Execute the last statement and capture its output
        last_stmt = statements[-1].strip()
        if last_stmt and not last_stmt.startswith('#'):
            # Execute the statement and capture output
            output = repl.run(last_stmt)
            print(f"\n[Tools] Raw output: {output}")
            
            # For get_columns, capture the actual columns
            if 'get_columns' in last_stmt:
                try:
                    columns = tools.get_columns('hmda')
                    output = {
                        'available_columns': columns,
                        'count': len(columns)
                    }
                    print(f"\n[Tools] Captured columns: {len(columns)} columns available")
                except Exception as e:
                    print(f"\n[Tools] Error getting columns: {str(e)}")
                    output = str(e)
            # For visualization functions, analyze the figure directly
            elif any(viz_func in last_stmt for viz_func in [
                'create_scatter_plot', 'create_line_plot', 'create_bar_plot',
                'create_histogram', 'create_box_plot', 'create_correlation_matrix'
            ]):
                if isinstance(output, dict) and 'figure' in output and 'filename' in output:
                    # Initialize output_paths if needed
                    if "output_paths" not in state:
                        state["output_paths"] = {"html": []}
                    
                    # Store HTML path
                    state["output_paths"]["html"].append(output["filename"])
                    
                    # Analyze the visualization directly using the figure object
                    print("\n[Tools] Analyzing visualization")
                    analysis_result = analysis_agent.analyze(output, data_type="visualization")
                    
                    if analysis_result["success"]:
                        output = "\n".join([
                            "Visualization created successfully.",
                            f"View at images/plotly_figures/{output['filename']}",
                            "",
                            *analysis_result["insights"]
                        ])
                    else:
                        output = "\n".join([
                            "Visualization created successfully.",
                            f"View at images/plotly_figures/{output['filename']}",
                            "",
                            "Unable to analyze visualization."
                        ])
                    
        # Process non-visualization outputs
        if not (isinstance(output, dict) and 'figure' in output and 'filename' in output):
            analysis_result = analysis_agent.analyze(output)
            if analysis_result and analysis_result["success"]:
                if analysis_result["data_type"] == "dict" and isinstance(output, dict) and "available_columns" in output:
                    # Special handling for get_columns output
                    output = "\n".join([
                        "Available Columns:",
                        "----------------",
                        f"Total columns: {output['count']}",
                        "",
                        "Columns:",
                        "--------",
                        "\n".join(f"- {col}" for col in output['available_columns'])
                    ])
                else:
                    # For other outputs, format the insights
                    output = "\n".join([
                        "Analysis Results:",
                        "----------------",
                        *analysis_result["insights"],
                        "",
                        "Metrics:",
                        "--------",
                        json.dumps(analysis_result["metrics"], indent=2)
                    ])
            else:
                output = f"Analysis failed: {analysis_result['error']}"
        
        # Store intermediate outputs with enhanced context
        if "intermediate_outputs" not in state:
            state["intermediate_outputs"] = []
        
        state["intermediate_outputs"].append({
            "step": len(state["intermediate_outputs"]) + 1,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "thought": thought,
            "code": code_block,
            "raw_output": str(output),
            "processed_output": output,
            "success": True
        })
        
        print(f"\n[Tools] Processed output:\n{output}")
        
    except Exception as e:
        error_msg = str(e)
        print(f"\n[Tools] Error executing code: {error_msg}")
        
        # Store error in intermediate outputs
        if "intermediate_outputs" not in state:
            state["intermediate_outputs"] = []
            
        state["intermediate_outputs"].append({
            "step": len(state["intermediate_outputs"]) + 1,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "thought": thought,
            "code": code_block,
            "error": error_msg,
            "success": False
        })
        
        # Analyze error using analysis agent
        analysis_result = analysis_agent.analyze(error_msg)
        if analysis_result["success"]:
            output = "\n".join([
                "Code Execution Error:",
                "-------------------",
                *analysis_result["insights"]
            ])
        else:
            output = f"Error: {error_msg}"
        
    # Format the completion message with the full output
    completion_msg = output if isinstance(output, str) else str(output)
    
    # Add the execution result to messages
    state["messages"].append(AIMessage(content=completion_msg))
    
    return state
