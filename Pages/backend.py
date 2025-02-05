from langchain_core.messages import HumanMessage
from typing import List
from dataclasses import dataclass
from langgraph.graph import StateGraph
from Pages.graph.state import AgentState
from Pages.graph.nodes import call_model, call_tools, route_to_tools
from Pages.data_models import InputData
from Pages.prompts.research_agent_role import ROLE_DEFINITION

class PythonChatbot:
    def __init__(self):
        super().__init__()
        self.reset_chat()
        self.graph = self.create_graph()
        self.role_definition = ROLE_DEFINITION
        
    def create_graph(self):
        workflow = StateGraph(AgentState)
        workflow.add_node('agent', call_model)
        workflow.add_node('tools', call_tools)

        workflow.add_node("end", lambda x: x)
        
        # Add conditional edges from agent node
        workflow.add_conditional_edges(
            'agent',
            route_to_tools,
            {
                "tools": "tools",
                "end": "end"
            }
        )
        
        # Add edge from tools back to agent
        workflow.add_edge('tools', 'agent')
        
        workflow.set_entry_point('agent')
        return workflow.compile()
    
    def user_sent_message(self, user_query, input_data: List[InputData]):
        print("\n[Backend] Processing new user message...")
        print(f"[Backend] User Query: {user_query}")
        
        # Get current paths
        starting_paths = {
            'pickle': set(sum([paths.get('pickle', []) for paths in self.output_paths.values()], [])),
            'html': set(sum([paths.get('html', []) for paths in self.output_paths.values()], []))
        }
        
        input_state = {
            "messages": self.chat_history + [HumanMessage(content=f"User Query: {user_query}")],
            "output_paths": {"pickle": list(starting_paths['pickle']), "html": list(starting_paths['html'])},
            "input_data": input_data,
        }
        
        print("[Backend] Invoking graph workflow...")
        result = self.graph.invoke(input_state, {"recursion_limit": 25})
        print("[Backend] Graph workflow complete")
        self.chat_history = result["messages"]
        
        # Update paths with new files
        if "output_paths" in result:
            new_paths = {
                'pickle': set(result["output_paths"]["pickle"]) - starting_paths['pickle'],
                'html': set(result["output_paths"]["html"]) - starting_paths['html']
            }
            self.output_paths[len(self.chat_history) - 1] = {
                'pickle': list(new_paths['pickle']),
                'html': list(new_paths['html'])
            }
        if "intermediate_outputs" in result:
            self.intermediate_outputs.extend(result["intermediate_outputs"])

    def reset_chat(self):
        self.chat_history = []
        self.intermediate_outputs = []
        self.output_paths = {}
