from typing import List, TypedDict, Optional
from langchain_core.messages import BaseMessage
from Pages.data_models import InputData

class AgentState(TypedDict):
    messages: List[BaseMessage]
    output_image_paths: List[str]
    input_data: List[InputData]
    intermediate_outputs: Optional[List[dict]]
