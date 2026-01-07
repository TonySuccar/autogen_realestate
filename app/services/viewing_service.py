from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from app.models.viewing import Viewing, ViewingStatus
from app.models.property import Property
from app.middleware.logging import logger


def create_viewing(
    db: Session,
    property_id: int,
    scheduled_at: datetime,
) -> Dict[str, Any]:
    """
    Create a new viewing for a property
    
    Args:
        db: Database session
        property_id: ID of the property to view
        scheduled_at: Date and time for the viewing
        
    Returns:
        Dictionary with viewing details
        
    Raises:
        ValueError: If property doesn't exist or viewing conflicts with existing bookings
    """
    try:
        # Check if property exists
        property_exists = db.query(Property).filter(Property.id == property_id).first()
        if not property_exists:
            raise ValueError(f"Property with ID {property_id} does not exist")
        
        # Check for overlapping viewings (must have at least 1 hour gap)
        min_gap = timedelta(hours=1)
        time_range_start = scheduled_at - min_gap
        time_range_end = scheduled_at + min_gap
        
        conflicting_viewings = db.query(Viewing).filter(
            Viewing.property_id == property_id,
            Viewing.status == ViewingStatus.SCHEDULED,
            Viewing.scheduled_at >= time_range_start,
            Viewing.scheduled_at <= time_range_end
        ).all()
        
        if conflicting_viewings:
            # Format conflict information with property name
            conflicts = []
            for v in conflicting_viewings:
                time_str = v.scheduled_at.strftime('%B %d, %Y at %I:%M %p')
                conflicts.append(time_str)
            
            # Get property name for better error message
            property_name = property_exists.title
            conflict_list = ', '.join(conflicts)
            raise ValueError(
                f"Cannot book '{property_name}' at this time. "
                f"There's already a viewing scheduled at: {conflict_list}. "
                f"Please choose a time at least 1 hour before or after."
            )
        
        # Create new viewing
        viewing = Viewing(
            property_id=property_id,
            scheduled_at=scheduled_at,
            status=ViewingStatus.SCHEDULED
        )
        
        db.add(viewing)
        db.commit()
        db.refresh(viewing)
        
        logger.info(f"Created viewing {viewing.id} for property {property_id} at {scheduled_at}")
        
        return {
            "id": viewing.id,
            "property_id": viewing.property_id,
            "scheduled_at": viewing.scheduled_at,
            "status": viewing.status.value,
            "created_at": viewing.created_at
        }
    except ValueError:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating viewing: {e}")
        raise


def cancel_viewing(db: Session, viewing_id: int) -> Viewing:
    viewing = db.query(Viewing).filter(Viewing.id == viewing_id).first()
    if not viewing:
        raise ValueError("Viewing not found")

    viewing.status = ViewingStatus.CANCELLED
    db.commit()
    db.refresh(viewing)
    return viewing


def list_viewings(
    db: Session,
    property_id: Optional[int] = None,
    status: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    List viewings with optional filters
    
    Args:
        db: Database session
        property_id: Filter by property ID (optional)
        status: Filter by status (optional)
        
    Returns:
        List of viewing dictionaries
    """
    try:
        query = db.query(Viewing)
        
        if property_id is not None:
            query = query.filter(Viewing.property_id == property_id)
        
        if status is not None:
            # Convert string to enum if needed
            if isinstance(status, str):
                status = ViewingStatus(status)
            query = query.filter(Viewing.status == status)
        
        viewings = query.order_by(Viewing.scheduled_at.desc()).all()
        
        return [
            {
                "id": viewing.id,
                "property_id": viewing.property_id,
                "scheduled_at": viewing.scheduled_at,
                "status": viewing.status.value,
                "created_at": viewing.created_at,
                "updated_at": viewing.updated_at
            }
            for viewing in viewings
        ]
    except Exception as e:
        logger.error(f"Error listing viewings: {e}")
        raise
