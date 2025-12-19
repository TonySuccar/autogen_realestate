from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional
from app.db.database import get_db
from app.services.property_service import list_properties, get_property

router = APIRouter(prefix="/properties", tags=["properties"])


@router.get("/")
async def search_properties(
    city: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """
    Search for properties with optional filters.
    
    - **city**: Filter by city name (case-insensitive)
    - **min_price**: Minimum price
    - **max_price**: Maximum price
    """
    properties = list_properties(db, city=city, min_price=min_price, max_price=max_price)
    
    # Format response to hide database IDs
    formatted_properties = []
    for prop in properties:
        formatted_properties.append({
            "title": prop.title,
            "city": prop.city,
            "price": prop.price,
            "size_sqft": prop.size_sqft,
            "description": prop.description
        })
    
    return formatted_properties


@router.get("/{property_id}")
async def get_property_details(
    property_id: int,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific property.
    """
    property = get_property(db, property_id)
    
    if not property:
        return {"error": "Property not found"}
    
    return {
        "title": property.title,
        "city": property.city,
        "price": property.price,
        "size_sqft": property.size_sqft,
        "description": property.description
    }
