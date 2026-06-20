from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
import datetime
from ..database import Base

class AuthenticationEvent(Base):
    __tablename__ = "zerotrustforge_auth_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    device_id = Column(String)
    ip_address = Column(String)
    context_anomalies = Column(Integer)
    trust_score = Column(Float)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class MicroSegment(Base):
    __tablename__ = "zerotrustforge_microsegments"

    id = Column(Integer, primary_key=True, index=True)
    source_segment = Column(String, index=True)
    target_segment = Column(String, index=True)
    is_whitelisted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class AccessRequest(Base):
    __tablename__ = "zerotrustforge_access_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    resource_id = Column(String)
    required_trust_score = Column(Float)
    user_trust_score = Column(Float)
    access_granted = Column(Boolean)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class SecurityPolicyAction(Base):
    __tablename__ = "zerotrustforge_policy_actions"

    id = Column(Integer, primary_key=True, index=True)
    trigger_event = Column(String)
    action_taken = Column(String)
    target_user = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
