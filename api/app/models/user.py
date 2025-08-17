from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), default="student")  # student, mentor, owner
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    twofa_secret = Column(String(32), nullable=True)
    profile_data = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    applications = relationship("Application", back_populates="user")
    documents = relationship("Document", back_populates="owner")
    tasks = relationship("Task", back_populates="user")
    rules = relationship("Rule", back_populates="owner")
    user_skills = relationship("UserSkill", back_populates="user")

class Skill(Base):
    __tablename__ = "skills"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    category = Column(String(50))
    
    user_skills = relationship("UserSkill", back_populates="skill")

class UserSkill(Base):
    __tablename__ = "user_skills"
    
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    skill_id = Column(Integer, ForeignKey("skills.id"), primary_key=True)
    weight = Column(Integer, default=1)  # 1-5 proficiency
    
    user = relationship("User", back_populates="user_skills")
    skill = relationship("Skill", back_populates="user_skills")