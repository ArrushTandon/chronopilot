from pydantic import BaseModel
from typing import Optional, List

class OrchestrationRequest(BaseModel):
    user_id: str
    message: str
    conversation_history: Optional[List[dict]] = []

class OrchestrationResponse(BaseModel):
    reply: str
    agents_invoked: List[str]
    tasks_created: List[dict]
    execution_log: List[str]
    session_id: Optional[str] = None

class TaskCreate(BaseModel):
    user_id: str
    title: str
    description: Optional[str] = ""
    priority_label: Optional[str] = "medium"
    estimated_hours: Optional[float] = 1.0
    deadline: Optional[str] = None