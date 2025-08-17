from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum

class OpportunityType(str, enum.Enum):
    INTERNSHIP = "internship"
    JOB = "job"
    RESEARCH = "research"
    FELLOWSHIP = "fellowship"

class WorkMode(str, enum.Enum):
    REMOTE = "remote"
    ONSITE = "onsite"
    HYBRID = "hybrid"

class Organization(Base):
    __tablename__ = "organizations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    website = Column(String(500))
    type = Column(String(100))  # startup, corporation, university, lab
    location = Column(String(255))
    description = Column(Text)
    logo_url = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    opportunities = relationship("Opportunity", back_populates="organization")
    contacts = relationship("Contact", back_populates="organization")

class Opportunity(Base):
    __tablename__ = "opportunities"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    title = Column(String(255), nullable=False, index=True)
    kind = Column(SQLEnum(OpportunityType), nullable=False)
    location = Column(String(255))
    mode = Column(SQLEnum(WorkMode), default=WorkMode.ONSITE)
    url = Column(String(500))
    deadline_at = Column(DateTime(timezone=True))
    jd_text = Column(Text)
    requirements = Column(JSON, default=[])
    skills_required = Column(JSON, default=[])
    salary_min = Column(Integer)
    salary_max = Column(Integer)
    source = Column(String(100))  # scraped, manual, imported
    status = Column(String(50), default="active")  # active, expired, filled
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization", back_populates="opportunities")
    applications = relationship("Application", back_populates="opportunity")