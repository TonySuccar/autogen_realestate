"""
AutoGen-based Booking Agent
"""
from autogen import ConversableAgent
from sqlalchemy.orm import Session
from typing import Optional, Annotated
from datetime import datetime
from app.services.viewing_service import create_viewing, list_viewings
from app.services.property_service import find_property_by_name
from app.agents.autogen_config import get_llm_config, get_agent_system_messages
from app.middleware.logging import logger
from app.models.property import Property


def create_property_viewing(
    db: Session,
    property_name: str,
    date: str,
    time: str,
    user_id: int = 1
) -> str:
    """
    Schedule a property viewing
    
    Args:
        db: Database session
        property_name: Name or title of the property (e.g., 'Downtown Loft')
        date: Date in YYYY-MM-DD format
        time: Time in HH:MM format (24-hour)
        user_id: ID of the user booking (default=1)
        
    Returns:
        Formatted confirmation message
    """
    try:
        # Find property by name
        property_obj = find_property_by_name(db, property_name)
        
        datetime_str = f"{date} {time}"
        scheduled_at = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
        
        viewing = create_viewing(db, property_obj.id, scheduled_at)
        
        # Format the datetime nicely
        nice_date = scheduled_at.strftime("%A, %B %d, %Y")
        nice_time = scheduled_at.strftime("%I:%M %p")
        
        return f"""✅ **Viewing Scheduled Successfully!**

🏠 **Property:** {property_obj.title}
📍 **Location:** {property_obj.city}
📅 **Date:** {nice_date}
⏰ **Time:** {nice_time}
🎫 **Confirmation Number:** #{viewing['id']}

💡 **What's next?**
- You'll receive a confirmation email
- Add this to your calendar
- Feel free to reschedule if needed!

Looking forward to showing you this property! 🏡"""
        
    except ValueError as e:
        logger.error(f"Property lookup error: {e}")
        return f"❌ {str(e)}\n\nPlease check the property name and try again, or search for properties first!"
    except Exception as e:
        logger.error(f"Error creating viewing: {e}")
        return f"❌ Oops! I couldn't schedule that viewing. {str(e)}\n\nPlease try again or search for properties first!"


def list_user_viewings(db: Session, user_id: int = 1) -> str:
    """
    List all viewings for a user
    
    Args:
        db: Database session
        user_id: ID of the user (default=1)
        
    Returns:
        Formatted list of viewings
    """
    try:
        viewings = list_viewings(db)
        
        if not viewings:
            return "📅 You don't have any scheduled viewings yet.\n\n💡 Ready to book one? Just let me know which property you're interested in!"
        
        result = f"📅 **Your Upcoming Viewings** ({len(viewings)} scheduled)\n\n"
        
        for idx, v in enumerate(viewings, 1):
            sched_time = datetime.fromisoformat(v["scheduled_at"])
            nice_date = sched_time.strftime("%A, %b %d")
            nice_time = sched_time.strftime("%I:%M %p")
            
            # Get property details
            prop = db.query(Property).filter(Property.id == v['property_id']).first()
            property_name = prop.title if prop else f"Property #{v['property_id']}"
            
            result += f"**{idx}. {property_name}**\n"
            result += f"   📅 {nice_date} at {nice_time}\n"
            result += f"   📋 Status: {v['status'].title()}\n"
            result += f"   🎫 Confirmation: #{v['id']}\n\n"
        
        result += "\n💡 Need to reschedule or cancel? Just let me know!"
        return result
        
    except Exception as e:
        logger.error(f"Error listing viewings: {e}")
        return "❌ I had trouble retrieving your viewings. Please try again!"


class BookingAgentAutogen:
    """
    AutoGen-based Booking/Viewing Scheduler Agent
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.system_message = get_agent_system_messages()["booking_agent"]
        
        # Create wrapper functions with Annotated type hints for AutoGen tool calling
        def create_viewing_wrapper(
            property_name: Annotated[str, "Name or title of the property (e.g., 'Downtown Loft', 'Modern Villa'). Extract from user's message."],
            date: Annotated[str, "Date in YYYY-MM-DD format (e.g., 2025-12-25)"],
            time: Annotated[str, "Time in HH:MM format 24-hour (e.g., 14:30 for 2:30 PM, 20:00 for 8:00 PM)"],
            user_id: Annotated[int, "User ID (default 1)"] = 1
        ) -> str:
            return create_property_viewing(self.db, property_name, date, time, user_id)
        
        def list_viewings_wrapper(
            user_id: Annotated[int, "User ID to list viewings for (default 1)"] = 1
        ) -> str:
            return list_user_viewings(self.db, user_id)
        
        # Create AutoGen conversable agent with function calling
        self.agent = ConversableAgent(
            name="BookingAgent",
            system_message=self.system_message,
            llm_config=get_llm_config(),
            human_input_mode="NEVER",
            max_consecutive_auto_reply=5,
        )
        
        # Register tools using new AutoGen API
        self.agent.register_for_llm(
            name="create_viewing",
            description="Schedule a property viewing appointment with specific date and time"
        )(create_viewing_wrapper)
        
        self.agent.register_for_llm(
            name="list_viewings",
            description="List all scheduled viewings for a user"
        )(list_viewings_wrapper)
        
        # Register for execution
        self.agent.register_for_execution(
            name="create_viewing"
        )(create_viewing_wrapper)
        
        self.agent.register_for_execution(
            name="list_viewings"
        )(list_viewings_wrapper)
