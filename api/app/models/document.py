from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False, index=True)
    kind = Column(String(50), nullable=False)  # resume, cover_letter, portfolio, transcript
    version = Column(Integer, default=1)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)
    mime_type = Column(String(100))
    content_text = Column(Text)  # Extracted text content
    word_count = Column(Integer, default=0)
    tags = Column(JSON, default=[])
    embeddings = Column(JSON)  # Vector embeddings for semantic search
    is_template = Column(Boolean, default=False)
    template_variables = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    owner = relationship("User", back_populates="documents")