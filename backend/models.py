from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text
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

class Batch(Base):
    __tablename__ = "batches"
    
    id = Column(String, primary_key=True, index=True)  # UUID string
    user_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String, default='pending')  # pending, processing, done, error
    created_at = Column(DateTime, default=datetime.utcnow)
    
    owner = relationship("User")
    jobs = relationship("ProcessingJob", back_populates="batch")

class Dictionary(Base):
    __tablename__ = "dictionaries"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    is_active = Column(Boolean, default=False)
    hs_code_prefixes = Column(String, nullable=True)  # Comma-separated 4-digit HS prefixes e.g. "8539,9405,7020"
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
    batch_id = Column(String, ForeignKey("batches.id"), nullable=True)
    transaction_type = Column(String, nullable=True)  # 'Nhập khẩu' or 'Xuất khẩu'
    created_at = Column(DateTime, default=datetime.utcnow)
    
    total_rows = Column(Integer, nullable=True)
    total_columns = Column(Integer, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    error_message = Column(String, nullable=True)
    
    owner = relationship("User", back_populates="jobs")
    dictionary = relationship("Dictionary")
    batch = relationship("Batch", back_populates="jobs")

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

class HSCustomsReference(Base):
    __tablename__ = "hs_customs_reference"
    
    hs_code = Column(String, primary_key=True, index=True)
    level = Column(Integer, index=True)
    description_vn = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
