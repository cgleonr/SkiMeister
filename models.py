"""
Database models for SkiMeister
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Resort(Base):
    """Ski resort information"""
    __tablename__ = 'resorts'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False, index=True)
    slug = Column(String(200), unique=True, nullable=False, index=True)
    country = Column(String(100), nullable=False, index=True)
    region = Column(String(200))
    
    # Location
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    
    # Altitude
    altitude_min = Column(Integer)  # meters
    altitude_max = Column(Integer)  # meters
    
    # General info
    website = Column(String(500))
    description = Column(String(1000))
    
    # Relationships
    conditions = relationship('Conditions', back_populates='resort', uselist=False, cascade='all, delete-orphan')
    pricing = relationship('Pricing', back_populates='resort', uselist=False, cascade='all, delete-orphan')
    forecasts = relationship('Forecast', back_populates='resort', cascade='all, delete-orphan')
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self, include_conditions=True, include_pricing=True, include_forecasts=True):
        """Convert to dictionary for JSON serialization"""
        data = {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'country': self.country,
            'region': self.region,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'altitude_min': self.altitude_min,
            'altitude_max': self.altitude_max,
            'website': self.website,
            'description': self.description
        }
        
        if include_conditions and self.conditions:
            data['conditions'] = self.conditions.to_dict()
        
        if include_pricing and self.pricing:
            data['pricing'] = self.pricing.to_dict()
            
        if include_forecasts and self.forecasts:
            data['forecasts'] = [f.to_dict() for f in sorted(self.forecasts, key=lambda x: x.date)]
        
        return data


class Conditions(Base):
    """Current snow and weather conditions"""
    __tablename__ = 'conditions'
    
    id = Column(Integer, primary_key=True)
    resort_id = Column(Integer, ForeignKey('resorts.id'), nullable=False, unique=True)
    
    # Snow conditions
    snow_depth_valley = Column(Integer)  # cm
    snow_depth_mountain = Column(Integer)  # cm
    fresh_snow_24h = Column(Integer)  # cm
    fresh_snow_48h = Column(Integer)  # cm
    
    # Weather
    temperature_valley = Column(Float)  # celsius
    temperature_mountain = Column(Float)  # celsius
    wind_speed = Column(Integer)  # km/h
    visibility = Column(String(50))  # good, moderate, poor
    
    # Slopes and lifts
    slopes_open_km = Column(Float)
    slopes_total_km = Column(Float)
    lifts_open = Column(Integer)
    lifts_total = Column(Integer)
    
    # Status
    status = Column(String(50))  # open, closed, partial
    
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    resort = relationship('Resort', back_populates='conditions')
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'snow_depth_valley': self.snow_depth_valley,
            'snow_depth_mountain': self.snow_depth_mountain,
            'fresh_snow_24h': self.fresh_snow_24h,
            'fresh_snow_48h': self.fresh_snow_48h,
            'temperature_valley': self.temperature_valley,
            'temperature_mountain': self.temperature_mountain,
            'wind_speed': self.wind_speed,
            'visibility': self.visibility,
            'slopes_open_km': self.slopes_open_km,
            'slopes_total_km': self.slopes_total_km,
            'lifts_open': self.lifts_open,
            'lifts_total': self.lifts_total,
            'status': self.status,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }


class Pricing(Base):
    """Ticket pricing information"""
    __tablename__ = 'pricing'
    
    id = Column(Integer, primary_key=True)
    resort_id = Column(Integer, ForeignKey('resorts.id'), nullable=False, unique=True)
    
    # Prices
    adult_day_pass = Column(Float)
    child_day_pass = Column(Float)
    currency = Column(String(10), default='EUR')
    
    # Season info
    season_start = Column(String(50))
    season_end = Column(String(50))
    
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    resort = relationship('Resort', back_populates='pricing')
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'adult_day_pass': self.adult_day_pass,
            'child_day_pass': self.child_day_pass,
            'currency': self.currency,
            'season_start': self.season_start,
            'season_end': self.season_end,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }


class Forecast(Base):
    """Weather and snow forecast for the resort"""
    __tablename__ = 'forecasts'
    
    id = Column(Integer, primary_key=True)
    resort_id = Column(Integer, ForeignKey('resorts.id'), nullable=False)
    
    date = Column(DateTime, nullable=False)
    
    # Weather forecast
    temp_min = Column(Float)
    temp_max = Column(Float)
    symbol = Column(String(50))  # e.g., 'sunny', 'snowy', etc.
    
    # Snow forecast
    snow_forecast_cm = Column(Integer)
    
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    resort = relationship('Resort', back_populates='forecasts')
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'date': self.date.isoformat() if self.date else None,
            'temp_min': self.temp_min,
            'temp_max': self.temp_max,
            'symbol': self.symbol,
            'snow_forecast_cm': self.snow_forecast_cm
        }
