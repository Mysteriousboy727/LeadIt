from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text

from .db import Base


class Lead(Base):
    __tablename__ = "leads"
    id = Column(Integer, primary_key=True)
    dedupe_key = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(255), index=True)
    phone = Column(String(64))
    address = Column(Text)
    area = Column(String(128), index=True)
    city = Column(String(128), index=True)
    state = Column(String(128))
    pincode = Column(String(16), index=True)
    maps_url = Column(Text)
    website = Column(Text)
    category = Column(Text)
    business_type = Column(String(128), index=True)
    lat = Column(Float)
    lng = Column(Float)
    distance_km = Column(Float)
    ring = Column(String(16))
    confidence = Column(Float, default=0)
    tier = Column(String(16), index=True)
    sources = Column(String(64))
    created_at = Column(DateTime, default=datetime.utcnow)


class Search(Base):
    __tablename__ = "searches"
    id = Column(Integer, primary_key=True)
    business_type = Column(String(128), nullable=False)
    location = Column(String(255), nullable=False)
    requested = Column(Integer, nullable=False)
    found = Column(Integer, default=0)
    new_count = Column(Integer, default=0)
    status = Column(String(16), default="queued")  # queued / running / completed / failed
    stage = Column(String(24), default="queued")
    place_label = Column(String(255))
    log = Column(Text, default="")
    error = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
