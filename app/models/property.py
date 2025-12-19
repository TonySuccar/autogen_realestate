from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from app.db.database import Base


class Property(Base):
    """Minimal Property model (AutoGen testing only)"""
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)

    # Core searchable fields
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Basic filters
    city = Column(String(100), nullable=False, index=True)
    price = Column(Float, nullable=False)
    size_sqft = Column(Float, nullable=True)

    # Ownership
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<Property(id={self.id}, title='{self.title}', city='{self.city}', price={self.price})>"
