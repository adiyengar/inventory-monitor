"""Database models for inventory tracking"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

class VideoRecord(Base):
    __tablename__ = 'video_records'
    
    id = Column(Integer, primary_key=True)
    filename = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    processed_at = Column(DateTime, default=datetime.now)
    duration_seconds = Column(Float)
    frames_processed = Column(Integer)
    success = Column(Boolean, default=True)

class InventorySnapshot(Base):
    __tablename__ = 'inventory_snapshots'
    
    id = Column(Integer, primary_key=True)
    video_id = Column(Integer)
    drawer_id = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    part_count = Column(Integer, nullable=False)
    confidence = Column(Float)
    status = Column(String)  # OK, WARNING, CRITICAL

class Alert(Base):
    __tablename__ = 'alerts'
    
    id = Column(Integer, primary_key=True)
    drawer_id = Column(String, nullable=False)
    alert_type = Column(String, nullable=False)  # CRITICAL, WARNING
    part_count = Column(Integer)
    threshold = Column(Integer)
    created_at = Column(DateTime, default=datetime.now)
    sent_at = Column(DateTime)
    resolved_at = Column(DateTime)

def init_database(db_path='data/inventory_tracking.db'):
    engine = create_engine(f'sqlite:///{db_path}')
    Base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine)
