from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Contact(Base):
    __tablename__ = "contacts"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), index=True)
    phone = Column(String(50))
    role = Column(String(100))  # recruiter, engineer, manager, etc.
    notes = Column(Text)
    last_contacted_at = Column(DateTime(timezone=True))
    strength = Column(Integer, default=1)  # 1-5 relationship strength
    tags = Column(JSON, default=[])
    linkedin_url = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization", back_populates="contacts")
    interactions = relationship("ContactInteraction", back_populates="contact")

class ContactInteraction(Base):
    __tablename__ = "contact_interactions"
    
    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False)
    type = Column(String(50), nullable=False)  # email, call, meeting, linkedin
    direction = Column(String(20), default="outbound")  # inbound, outbound
    subject = Column(String(255))
    notes = Column(Text)
    at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    contact = relationship("Contact", back_populates="interactions")