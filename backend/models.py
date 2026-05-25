from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
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
    is_active = Column(Boolean, default=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    owner = relationship("User", back_populates="dictionaries")

class DictionaryUsage(Base):
    __tablename__ = "dictionary_usage"
    
    id = Column(Integer, primary_key=True, index=True)
    dictionary_id = Column(Integer, ForeignKey("dictionaries.id"))
    job_id = Column(String, ForeignKey("processing_jobs.id"))
    used_at = Column(DateTime, default=datetime.utcnow)
    
    dictionary = relationship("Dictionary")
    job = relationship("ProcessingJob")

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

class HSTaxonomy(Base):
    __tablename__ = "hs_taxonomy"
    
    id = Column(Integer, primary_key=True, index=True)
    hs_code_prefix = Column(String, unique=True, index=True, nullable=False)
    dong_sp = Column(String, nullable=False)  # Product Line e.g. "SP ĐÈN/BÓNG ĐÈN"
    industry_name = Column(String, nullable=False)  # Lớp 1 e.g. "Bóng đèn LED"
    default_type = Column(String, nullable=False)  # "NC" or "LK"
    source = Column(String, default='system')  # "system", "crawled", "user_input"
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
