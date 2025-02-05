from dataclasses import dataclass
from typing import List, Optional

@dataclass
class InputData:
    variable_name: str
    data_path: str
    data_description: Optional[str] = None
