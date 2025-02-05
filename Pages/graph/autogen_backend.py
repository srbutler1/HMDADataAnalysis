from typing import List, Dict, Any
from Pages.data_models import InputData
from Pages.graph.agents import create_agents
from Pages.graph.group_chat import create_group_chat
from Pages.graph.tools import DataAnalysisTools
import autogen

class AutoGenBackend:
    def __init__(self):
        """Initialize with empty state"""
        self.reset()
        
    def reset(self):
        """Reset the backend state"""
        self.chat_history = []
        self.intermediate_outputs = []
        self.output_paths = {}
        self.tools = None
        self.group_chat = None
        self.manager = None
        self.planner = None
        self.executor = None
        self.analyzer = None
        self.user_proxy = None
        self._is_initialized = False
        
    def initialize_agents(self, config_list):
        """Initialize the agent team with configuration"""
        try:
            # Create agents
            seed = 42  # For reproducibility
            self.planner, self.executor, self.analyzer, self.user_proxy = create_agents(config_list, seed)
            
            # Create agent group chat and manager
            agents = [self.planner, self.executor, self.analyzer, self.user_proxy]
            group_chat_result = create_group_chat(agents, config_list, seed)
            
            if not group_chat_result or len(group_chat_result) != 2:
                raise ValueError("Failed to create group chat - invalid return value")
                
            self.group_chat, self.manager = group_chat_result
            
            if not self.group_chat or not self.manager:
                raise ValueError("Failed to create group chat or manager")
                
            # Initialize messages list
            self.group_chat.messages = []
            self._is_initialized = True
            print("[Backend] Successfully initialized agents and group chat")
            return True
            
        except Exception as e:
            print(f"[Backend] Error initializing agents: {str(e)}")
            self.reset()
            return False

    def process_query(self, user_query: str, input_data: List[InputData]) -> Dict[str, Any]:
        """Process a user query using the agent team"""
        if not self._is_initialized:
            return {
                'success': False,
                'error': "Backend not initialized",
                'messages': [],
                'output_paths': {},
                'intermediate_outputs': []
            }
        
        try:
            # Initialize tools with input data
            self.tools = DataAnalysisTools(input_data)
            
            # Create function map
            function_map = {
                "get_columns": lambda: self.tools.get_columns('hmda'),
                "create_scatter_plot": lambda x_col, y_col, title=None: self.tools.create_scatter_plot('hmda', x_col, y_col, title),
                "create_line_plot": lambda x_col, y_col, title=None: self.tools.create_line_plot('hmda', x_col, y_col, title),
                "create_bar_plot": lambda x_col, y_col, title=None, group_by=None: self.tools.create_bar_plot('hmda', x_col, y_col, title, group_by),
                "create_histogram": lambda column, bins=30, title=None: self.tools.create_histogram('hmda', column, bins, title),
                "create_box_plot": lambda column, title=None, group_by=None: self.tools.create_box_plot('hmda', column, title, group_by),
                "calculate_summary_stats": lambda columns=None, group_by=None: self.tools.calculate_summary_stats('hmda', columns, group_by),
                "calculate_correlation": lambda col1, col2: self.tools.calculate_correlation('hmda', col1, col2),
                "create_correlation_matrix": lambda columns=None: self.tools.create_correlation_matrix('hmda', columns)
            }
            
            # Register functions with user proxy
            self.user_proxy.register_function(function_map)
            
            # Store user query
            self.chat_history.append({
                'role': 'user',
                'content': user_query
            })
            
            # Prepare the initial message
            initial_message = f"""Task: {user_query}

Available Data:
- Dataset loaded with {len(self.tools.dataframes['hmda'])} rows

Available functions (no need to specify 'hmda' as dataset):
- get_columns()  # Check available columns first
- create_scatter_plot(x_col, y_col, title=None)
- create_line_plot(x_col, y_col, title=None)
- create_bar_plot(x_col, y_col, title=None, group_by=None)
- create_histogram(column, bins=30, title=None)
- create_box_plot(column, title=None, group_by=None)
- calculate_summary_stats(columns=None, group_by=None)
- calculate_correlation(col1, col2)
- create_correlation_matrix(columns=None)

First, check the available columns using get_columns().
Then use the other functions as needed.

Planner: Please break this task down into clear steps."""

            # Run the group chat
            self.group_chat.messages = []
            chat_result = self.manager.run(initial_message)
            
            # Store ALL messages from the group chat
            raw_messages = []
            for msg in self.group_chat.messages:
                if isinstance(msg, dict):
                    raw_messages.append(msg)
                else:
                    raw_messages.append({
                        'role': getattr(msg, 'role', getattr(msg, 'name', 'unknown')),
                        'content': getattr(msg, 'content', str(msg))
                    })
            
            return {
                'success': True,
                'messages': self.chat_history,
                'raw_messages': raw_messages,  # Include raw messages
                'output_paths': self.output_paths,
                'intermediate_outputs': self.intermediate_outputs
            }
            
        except Exception as e:
            print(f"Error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'messages': self.chat_history,
                'raw_messages': [],
                'output_paths': self.output_paths,
                'intermediate_outputs': self.intermediate_outputs
            }
    
    def get_chat_history(self) -> List[Dict[str, str]]:
        """Get the full chat history"""
        return self.chat_history
    
    def get_output_paths(self) -> Dict[int, Dict[str, List[str]]]:
        """Get all output file paths"""
        return self.output_paths
    
    def get_intermediate_outputs(self) -> List[Dict[str, Any]]:
        """Get all intermediate processing outputs"""
        return self.intermediate_outputs
