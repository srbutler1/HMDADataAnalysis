from dataclasses import dataclass
from typing import Optional, List

@dataclass
class InputData:
    """Data class for input data information"""
    variable_name: str
    data_path: str
    data_description: Optional[str] = None
    
    def __post_init__(self):
        """Validate the input data after initialization"""
        if not self.variable_name:
            raise ValueError("variable_name cannot be empty")
        if not self.data_path:
            raise ValueError("data_path cannot be empty")
