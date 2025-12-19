from sqlalchemy.orm import Session
from app.models.property import Property


def list_properties(
    db: Session,
    city: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
):
    query = db.query(Property)

    if city:
        query = query.filter(Property.city.ilike(f"%{city}%"))
    if min_price is not None:
        query = query.filter(Property.price >= min_price)
    if max_price is not None:
        query = query.filter(Property.price <= max_price)

    return query.all()


def get_property(db: Session, property_id: int) -> Property:
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise ValueError("Property not found")
    return prop


def find_property_by_name(db: Session, property_name: str) -> Property:
    """
    Find a property by name/title with smart fuzzy matching
    
    Args:
        db: Database session
        property_name: Property name or partial name to search for
        
    Returns:
        Property object
        
    Raises:
        ValueError: If property not found or multiple matches
    """
    search_term = property_name.strip()
    
    # Strategy 1: Exact match (case-insensitive)
    prop = db.query(Property).filter(Property.title.ilike(search_term)).first()
    if prop:
        return prop
    
    # Strategy 2: Partial match in title
    matches = db.query(Property).filter(Property.title.ilike(f"%{search_term}%")).all()
    
    # Strategy 3: If no title matches, search in description too
    if not matches:
        matches = db.query(Property).filter(
            (Property.title.ilike(f"%{search_term}%")) | 
            (Property.description.ilike(f"%{search_term}%"))
        ).all()
    
    # Strategy 4: Try matching individual words (for typos like "new tork" → "new york")
    if not matches:
        words = search_term.lower().split()
        if len(words) > 1:
            # Match properties that contain all words (in any order)
            query = db.query(Property)
            for word in words:
                query = query.filter(
                    (Property.title.ilike(f"%{word}%")) | 
                    (Property.description.ilike(f"%{word}%")) |
                    (Property.city.ilike(f"%{word}%"))
                )
            matches = query.all()
    
    # Strategy 5: Try just the city name
    if not matches and len(search_term.split()) > 1:
        # Extract likely city names (common patterns)
        for word in search_term.split():
            city_matches = db.query(Property).filter(Property.city.ilike(f"%{word}%")).all()
            if city_matches:
                matches = city_matches
                break
    
    if not matches:
        # Provide helpful error with suggestions
        all_props = db.query(Property).limit(5).all()
        suggestions = [f"'{p.title}'" for p in all_props]
        raise ValueError(
            f"I couldn't find a property matching '{property_name}'. "
            f"Try searching for properties first! Here are some available: {', '.join(suggestions)}"
        )
    
    if len(matches) == 1:
        return matches[0]
    
    # Multiple matches - try to narrow down
    # Prefer exact word matches in title
    exact_word_matches = [
        p for p in matches 
        if any(word.lower() in p.title.lower() for word in search_term.split())
    ]
    
    if len(exact_word_matches) == 1:
        return exact_word_matches[0]
    
    # Return best match if we found some, otherwise show options
    if len(matches) <= 3:
        titles = [f"'{p.title}' in {p.city}" for p in matches]
        raise ValueError(f"Found these properties: {', '.join(titles)}. Which one did you mean?")
    else:
        titles = [f"'{p.title}' in {p.city}" for p in matches[:3]]
        raise ValueError(
            f"Found {len(matches)} properties. Here are the top matches: {', '.join(titles)}. "
            f"Please be more specific or search by city first!"
        )
    
    return matches[0]
