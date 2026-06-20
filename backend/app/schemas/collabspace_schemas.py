from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class WorkspaceCreate(BaseModel):
    name: str
    owner: str

class WorkspaceRead(WorkspaceCreate):
    id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class AnnotationCreate(BaseModel):
    workspace_id: int
    author: str
    content: str

class AnnotationRead(AnnotationCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
