from sqlalchemy import Column, Integer, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.sql import func
from app.db.database import Base
import enum


class ViewingStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Viewing(Base):
    __tablename__ = "viewings"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False, index=True)
    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    status = Column(SQLEnum(ViewingStatus), default=ViewingStatus.SCHEDULED, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
