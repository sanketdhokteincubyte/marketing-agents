from abc import ABC, abstractmethod
from typing import List, Optional
from fastapi import UploadFile

class BaseAgent(ABC):
    @abstractmethod
    def get_response(self, prompt: str, files: Optional[List[UploadFile]] = None) -> str:
        pass
