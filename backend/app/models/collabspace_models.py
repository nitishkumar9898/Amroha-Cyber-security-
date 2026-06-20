from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from ..database import Base

class InvestigationWorkspace(Base):
    __tablename__ = "collabspace_workspaces"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    owner = Column(String)
    status = Column(String, default="Active")
    created_at = Column(DateTime, default=datetime.utcnow)

class WorkspaceAnnotation(Base):
    __tablename__ = "collabspace_annotations"
    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer)
    author = Column(String)
    content = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
