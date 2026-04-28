from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default='user')
    
    dictionaries = relationship("Dictionary", back_populates="owner")
    jobs = relationship("ProcessingJob", back_populates="owner")

class Dictionary(Base):
    __tablename__ = "dictionaries"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    owner = relationship("User", back_populates="dictionaries")

class ProcessingJob(Base):
    __tablename__ = "processing_jobs"
    
    id = Column(String, primary_key=True, index=True) # UUID string
    filename = Column(String)
    status = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))
    dictionary_id = Column(Integer, ForeignKey("dictionaries.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    total_rows = Column(Integer, nullable=True)
    total_columns = Column(Integer, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    error_message = Column(String, nullable=True)
    
    owner = relationship("User", back_populates="jobs")
    dictionary = relationship("Dictionary")
