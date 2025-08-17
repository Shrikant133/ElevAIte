from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Application(Base):
    __tablename__ = "applications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), nullable=False)
    status = Column(String(50), default="to_apply", index=True)
    applied_at = Column(DateTime(timezone=True))
    notes = Column(Text)
    score_fit = Column(Float)  # 0-100 fit score
    resume_version_id = Column(Integer, ForeignKey("documents.id"))
    cover_letter_id = Column(Integer, ForeignKey("documents.id"))
    priority = Column(Integer, default=0)  # Higher = more priority
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="applications")
    opportunity = relationship("Opportunity", back_populates="applications")
    events = relationship("ApplicationEvent", back_populates="application")
    resume = relationship("Document", foreign_keys=[resume_version_id])
    cover_letter = relationship("Document", foreign_keys=[cover_letter_id])

class ApplicationEvent(Base):
    __tablename__ = "application_events"
    
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    type = Column(String(50), nullable=False)  # email, call, interview, assessment
    title = Column(String(255))
    description = Column(Text)
    at = Column(DateTime(timezone=True), server_default=func.now())
    payload_json = Column(JSON, default={})
    
    # Relationships
    application = relationship("Application", back_populates="events")