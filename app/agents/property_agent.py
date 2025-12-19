"""
AutoGen-based Property Agent
"""
from autogen import ConversableAgent
from sqlalchemy.orm import Session
from typing import Optional, Annotated
from app.services.property_service import list_properties, get_property
from app.agents.autogen_config import get_llm_config, get_agent_system_messages
from app.middleware.logging import logger


def search_properties(
    db: Session,
    city: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None
) -> str:
    """
    Search for properties matching criteria and return formatted results
    
    Args:
        db: Database session
        city: City to search in (None = all cities)
        min_price: Minimum price filter
        max_price: Maximum price filter
        
    Returns:
        Formatted string with property listings
    """
    try:
        properties = list_properties(db, city=city, min_price=min_price, max_price=max_price)
        
        if not properties:
            return "I couldn't find any properties matching your criteria. Try adjusting your search!"
        
        # Format results nicely
        result_text = f"🏡 **Found {len(properties)} amazing properties!**\n\n"
        
        for idx, prop in enumerate(properties[:10], 1):
            result_text += f"**{idx}. {prop.title}**\n"
            result_text += f"   📍 {prop.city}\n"
            result_text += f"   💰 ${prop.price:,.0f}\n"
            result_text += f"   📐 {prop.size_sqft:,.0f} sq ft\n"
            
            if prop.description:
                desc = prop.description[:120] + "..." if len(prop.description) > 120 else prop.description
                result_text += f"   ℹ️  {desc}\n"
            
            result_text += "\n"
        
        if len(properties) > 10:
            result_text += f"_...and {len(properties) - 10} more! Let me know if you'd like to narrow down the search._\n"
        
        result_text += "\n💡 **Want to know more?** Just ask about a specific property or book a viewing!"
        
        logger.info(f"Found {len(properties)} properties")
        return result_text
        
    except Exception as e:
        logger.error(f"Error searching properties: {e}")
        return "Oops! I had trouble searching for properties. Please try again!"


def get_property_details(db: Session, property_id: int) -> str:
    """
    Get detailed information about a specific property
    
    Args:
        db: Database session
        property_id: Database ID of the property
        
    Returns:
        Formatted property details string
    """
    try:
        prop = get_property(db, property_id)
        
        details = f"🏠 **{prop.title}**\n\n"
        details += f"📍 **Location:** {prop.city}\n"
        details += f"💰 **Price:** ${prop.price:,.0f}\n"
        details += f"📐 **Size:** {prop.size_sqft:,.0f} square feet\n\n"
        
        if prop.description:
            details += f"**About this property:**\n{prop.description}\n\n"
        
        details += f"_Listed on: {prop.created_at.strftime('%B %d, %Y')}_\n\n"
        details += f"💡 **Ready to schedule a viewing?** Just say something like:\n"
        details += f"   'Book a viewing for {prop.title}'"
        
        return details
        
    except ValueError:
        return f"I couldn't find a property with ID {property_id}. Please check the ID and try again!"
    except Exception as e:
        logger.error(f"Error getting property details: {e}")
        return "I had trouble retrieving those property details. Please try again!"


class PropertyAgentAutogen:
    """
    AutoGen-based Property Search Agent
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.system_message = get_agent_system_messages()["property_agent"]
        
        # Create wrapper functions with Annotated type hints
        def search_properties_wrapper(
            city: Annotated[Optional[str], "City name to search in (e.g., 'New York', 'London'). Leave None for all cities"] = None,
            min_price: Annotated[Optional[float], "Minimum price filter in dollars"] = None,
            max_price: Annotated[Optional[float], "Maximum price filter in dollars"] = None
        ) -> str:
            return search_properties(self.db, city, min_price, max_price)
        
        def get_property_details_wrapper(
            property_id: Annotated[int, "Database ID of the property to get details for"]
        ) -> str:
            return get_property_details(self.db, property_id)
        
        # Create AutoGen conversable agent
        self.agent = ConversableAgent(
            name="PropertyAgent",
            system_message=self.system_message,
            llm_config=get_llm_config(),
            human_input_mode="NEVER",
            max_consecutive_auto_reply=5,
        )
        
        # Register tools using new AutoGen API
        self.agent.register_for_llm(
            name="search_properties",
            description="Search for real estate properties. Can filter by city, minimum price, and maximum price. Returns formatted list of matching properties."
        )(search_properties_wrapper)
        
        self.agent.register_for_llm(
            name="get_property_details",
            description="Get complete details about a specific property using its ID number"
        )(get_property_details_wrapper)
        
        # Register for execution
        self.agent.register_for_execution(
            name="search_properties"
        )(search_properties_wrapper)
        
        self.agent.register_for_execution(
            name="get_property_details"
        )(get_property_details_wrapper)
