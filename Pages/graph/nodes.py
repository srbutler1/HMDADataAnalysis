from typing import Annotated, Sequence, TypedDict, Union
from langchain_core.messages import AIMessage, BaseMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_experimental.utilities import PythonREPL
from Pages.graph.tools import DataAnalysisTools
import os

def call_model(state):
    """Process the messages with the LLM"""
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a helpful data analysis assistant. You can help analyze data and create visualizations using Python.
        
When working with the data, you have access to these functions through the DataAnalysisTools class:

- create_scatter_plot(data_var, x_col, y_col, title=None)
- create_line_plot(data_var, x_col, y_col, title=None) 
- create_bar_plot(data_var, x_col, y_col, title=None)
- create_histogram(data_var, column, bins=30, title=None)
- create_box_plot(data_var, column, title=None)
- calculate_summary_stats(data_var, columns=None)
- calculate_correlation(data_var, col1, col2)
- create_correlation_matrix(data_var, columns=None)

The data_var parameter refers to the name of the dataset (without .csv extension).

You should:
1. Understand what analysis/visualization is being requested
2. Write Python code to perform the analysis using the available functions
3. Explain your findings from the analysis

Format your response as:
Thought: Your reasoning about what analysis to perform
Code: ```python
# Your code here
```
Analysis: Your interpretation of the results"""),
        MessagesPlaceholder(variable_name="messages"),
    ])
    
    llm = ChatOpenAI(
        model="gpt-4-1106-preview",
        temperature=0
    )
    
    response = llm.invoke(prompt.invoke({"messages": state["messages"]}))
    state["messages"].append(response)
    
    return state

def route_to_tools(state):
    """Route to tools if code execution is needed"""
    last_message = state["messages"][-1]
    if "```python" in last_message.content:
        return "tools"
    return None

def call_tools(state):
    """Execute the Python code and capture outputs"""
    last_message = state["messages"][-1]
    code_block = last_message.content.split("```python")[1].split("```")[0].strip()
    
    # Initialize tools with input data
    tools = DataAnalysisTools(state["input_data"])
    
    # Create a namespace with required imports and tools
    namespace = {
        "tools": tools,
        "state": state
    }
    
    # Execute the code
    repl = PythonREPL(_globals=namespace)
    try:
        output = repl.run(code_block)
        
        # Store intermediate outputs for debugging
        if "intermediate_outputs" not in state:
            state["intermediate_outputs"] = []
        state["intermediate_outputs"].append({
            "thought": last_message.content.split("Thought:")[1].split("Code:")[0].strip(),
            "code": code_block,
            "output": output
        })
        
    except Exception as e:
        output = f"Error: {str(e)}"
        
    # Add the execution result to messages
    state["messages"].append(AIMessage(content=f"Code execution complete. {output}"))
    
    return state
