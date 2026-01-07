"""
AutoGen-based Booking Agent
"""
from autogen import ConversableAgent
from sqlalchemy.orm import Session
from typing import Optional, Annotated
from datetime import datetime
import re
from app.services.viewing_service import create_viewing, list_viewings
from app.services.property_service import find_property_by_name
from app.agents.autogen_config import get_llm_config, get_agent_system_messages
from app.middleware.logging import logger
from app.models.property import Property
from app.observability.phoenix_tracer import trace_agent_action


def extract_property_from_history(conversation_history: list, position: int) -> Optional[str]:
    """
    Extract property name from conversation history based on position
    
    Args:
        conversation_history: List of conversation messages
        position: Position in the list (1-indexed), or -1 for last
        
    Returns:
        Property name or None if not found
    """
    try:
        # Look through conversation history for property listings
        # Pattern matches: "**1. Property Name**" (with markdown bold)
        for msg in reversed(conversation_history):
            content = msg.get("content", "")
            
            # Match property listings in format: **1. Property Name**
            pattern = r'\*\*(\d+)\.\s+([^\*]+)\*\*'
            matches = re.findall(pattern, content)
            
            if matches:
                # Convert matches to dict: {position: property_name}
                properties = {int(num): name.strip() for num, name in matches}
                
                logger.info(f"Found {len(properties)} properties in conversation: {list(properties.values())}")
                
                if position == -1:
                    # Return last property
                    last_pos = max(properties.keys())
                    logger.info(f"Returning last property (position {last_pos}): {properties[last_pos]}")
                    return properties[last_pos]
                elif position in properties:
                    logger.info(f"Returning property at position {position}: {properties[position]}")
                    return properties[position]
        
        logger.warning(f"No properties found in conversation history for position {position}")
        return None
    except Exception as e:
        logger.error(f"Error extracting property from history: {e}", exc_info=True)
        return None


def create_property_viewing(
    db: Session,
    property_name: str,
    date: str,
    time: str,
    user_id: int = 1,
    conversation_history: list = None
) -> str:
    """
    Schedule a property viewing
    
    Args:
        db: Database session
        property_name: Name or title of the property (e.g., 'Downtown Loft') or ordinal reference (e.g., 'second', '2nd', '2')
        date: Date in YYYY-MM-DD format
        time: Time in HH:MM format (24-hour)
        user_id: ID of the user booking (default=1)
        conversation_history: List of conversation messages to extract property names from ordinal references
        
    Returns:
        Formatted confirmation message
    """
    try:
        with trace_agent_action(
            "BookingAgent",
            "create_property_viewing",
            property_name=property_name,
            date=date,
            time=time,
            user_id=user_id
        ):
            # Smart ordinal reference detection - extract actual property name from conversation
            ordinal_map = {
                'first': 1, '1st': 1, '1': 1, 'one': 1,
                'second': 2, '2nd': 2, '2': 2, 'two': 2,
                'third': 3, '3rd': 3, '3': 3, 'three': 3,
                'fourth': 4, '4th': 4, '4': 4, 'four': 4,
                'fifth': 5, '5th': 5, '5': 5, 'five': 5,
                'sixth': 6, '6th': 6, '6': 6, 'six': 6,
                'seventh': 7, '7th': 7, '7': 7, 'seven': 7,
                'eighth': 8, '8th': 8, '8': 8, 'eight': 8,
                'ninth': 9, '9th': 9, '9': 9, 'nine': 9,
                'tenth': 10, '10th': 10, '10': 10, 'ten': 10,
                'last': -1
            }
            
            property_name_lower = property_name.lower().strip()
            
            # Check if it's an ordinal reference
            if property_name_lower in ordinal_map:
                position = ordinal_map[property_name_lower]
                
                # Extract property names from conversation history
                if conversation_history:
                    extracted_property = extract_property_from_history(conversation_history, position)
                    if extracted_property:
                        logger.info(f"Resolved ordinal '{property_name}' (position {position}) to '{extracted_property}'")
                        property_name = extracted_property
                    else:
                        return f"""❌ I couldn't find the property at position {position} in the recent conversation.

💡 **Tip:** Make sure you've searched for properties first, then tell me which one (e.g., "the second one", "book the first property")."""
                else:
                    return """❌ I need to see the property list first to know which one you mean.

💡 **Please search for properties first:**
- "Show me all properties"
- "Find properties in New York"
Then say "book the second one" or "book property #2" """
            
            # Find property by name
            property_obj = find_property_by_name(db, property_name)
            
            datetime_str = f"{date} {time}"
            try:
                scheduled_at = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
            except ValueError as parse_error:
                return f"""❌ **Invalid date/time format!**

Error: {str(parse_error)}

💡 Please use the correct format:
- Date: YYYY-MM-DD (e.g., 2026-01-15)
- Time: HH:MM in 24-hour format (e.g., 14:00 for 2 PM, 17:00 for 5 PM)
- Full example: "2026-01-15 14:00" """
            
            # Validate that the viewing is not in the past
            from datetime import datetime as dt
            now = dt.now()
            if scheduled_at < now:
                # Calculate "tomorrow" for helpful suggestion
                tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0)
                from datetime import timedelta
                tomorrow = tomorrow + timedelta(days=1)
                
                return f"""❌ **Cannot book viewing in the past!**

📅 You requested: {scheduled_at.strftime('%B %d, %Y at %I:%M %p')}
📅 Current time: {now.strftime('%B %d, %Y at %I:%M %p')}

💡 **Please provide a FUTURE date. Examples:**
- Tomorrow: "{tomorrow.strftime('%Y-%m-%d')} 14:00"
- Next week: "2026-01-15 14:00"
- Next month: "2026-02-10 10:00" """
            
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
        error_msg = str(e)
        # Add helpful guidance for common errors
        if "couldn't find" in error_msg.lower() or "not found" in error_msg.lower():
            return f"""❌ {error_msg}

💡 **Tips:**
1. First, search for properties: "Show me all properties"
2. Then book using the exact property name: "Book [Property Name] for [Date] at [Time]"

Example: "Book Luxury Downtown Apartment for 2026-01-15 at 14:00" """
        elif "conflicts with existing viewing" in error_msg.lower() or ("cannot book" in error_msg.lower() and "already a viewing" in error_msg.lower()):
            return f"""❌ **Time Conflict!**

{error_msg}

💡 **How to resolve:**
- Choose a time at least 1 hour before or after (e.g., 7:30 AM or 10:30 AM)
- Or select a different date
- Or book a different property"""
        return f"❌ {error_msg}"
    except Exception as e:
        logger.error(f"Error creating viewing: {e}", exc_info=True)
        return f"❌ I couldn't schedule that viewing due to an error. Please try again or search for properties first!"


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
    
    def __init__(self, db: Session, group_chat=None):
        self.db = db
        self.group_chat = group_chat  # Store reference to group chat for conversation history
        self.system_message = get_agent_system_messages()["booking_agent"]
        
        # Create wrapper functions with Annotated type hints for AutoGen tool calling
        def create_viewing_wrapper(
            property_name: Annotated[str, "Name or title of the property (e.g., 'Downtown Loft', 'Modern Villa') OR ordinal reference (e.g., 'second', '2nd', 'the first one'). Extract from user's message."],
            date: Annotated[str, "Date in YYYY-MM-DD format (e.g., 2026-01-12)"],
            time: Annotated[str, "Time in HH:MM format 24-hour (e.g., 14:30 for 2:30 PM, 20:00 for 8:00 PM)"],
            user_id: Annotated[int, "User ID (default 1)"] = 1
        ) -> str:
            try:
                logger.info(f"Booking wrapper called with: property={property_name}, date={date}, time={time}")
                
                # Get conversation history from group chat if available
                conversation_history = None
                if self.group_chat:
                    conversation_history = self.group_chat.messages
                
                result = create_property_viewing(self.db, property_name, date, time, user_id, conversation_history)
                logger.info(f"Booking successful: {result[:100]}...")
                return result
            except ValueError as e:
                # ValueError includes property lookup errors and time conflicts
                logger.error(f"Booking validation error: {e}", exc_info=True)
                error_msg = str(e)
                
                # Check if it's a time conflict
                if "conflicts with existing viewing" in error_msg.lower():
                    return f"""❌ **Time Conflict!**

{error_msg}

💡 **How to resolve:**
- Choose a different time (at least 1 hour before or after existing bookings)
- Or book a different property"""
                else:
                    # Other validation errors (property not found, etc.)
                    return f"❌ {error_msg}"
            except Exception as e:
                logger.error(f"Error in booking wrapper: {e}", exc_info=True)
                return f"❌ Booking failed: {str(e)}"
        
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
            max_consecutive_auto_reply=2,  # Reduced for faster responses
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
