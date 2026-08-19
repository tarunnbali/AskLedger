from typing import Optional, List
from pydantic import BaseModel


class HistoryMessage(BaseModel):
    role: str    # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    question: str
    history: Optional[List[HistoryMessage]] = []