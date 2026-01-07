"""
AutoGen-based Orchestrator with GroupChat
"""
from autogen import GroupChat, GroupChatManager, ConversableAgent
from sqlalchemy.orm import Session
from typing import List, Dict
from app.agents.property_agent import PropertyAgentAutogen
from app.agents.booking_agent import BookingAgentAutogen
from app.agents.faq_agent import FAQAgentAutogen
from app.agents.autogen_config import get_llm_config
from app.middleware.logging import logger
from app.observability.phoenix_tracer import trace_agent_action


class OrchestratorAgentAutogen:
    """
    AutoGen-based multi-agent orchestrator using GroupChat
    Coordinates between PropertyAgent, BookingAgent, and FAQAgent
    """
    
    def __init__(self, db: Session):
        self.db = db
        
        # Initialize specialized AutoGen agents
        logger.info("Initializing AutoGen agents...")
        self.property_agent = PropertyAgentAutogen(db)
        
        # Initialize group chat first (will be updated with reference later)
        self.group_chat = None
        
        # Pass None for now, will update after group chat is created
        self.booking_agent = BookingAgentAutogen(db, None)
        self.faq_agent = FAQAgentAutogen(db)
        
        # Create a user proxy agent to represent the user
        self.user_proxy = ConversableAgent(
            name="User",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=0,
            llm_config=False,  # User proxy doesn't need LLM
            code_execution_config=False,
        )
        
        # Create GroupChat with all agents
        self.group_chat = GroupChat(
            agents=[
                self.user_proxy,
                self.property_agent.agent,
                self.booking_agent.agent,
                self.faq_agent.agent
            ],
            messages=[],
            max_round=3,  # Reduced for faster responses
            speaker_selection_method="auto",  # Let AutoGen decide who speaks
            allow_repeat_speaker=False,  # Prevent agents from monopolizing conversation
        )
        
        # Now update booking agent with group chat reference
        self.booking_agent.group_chat = self.group_chat
        
        # Create manager to coordinate the group chat
        self.manager = GroupChatManager(
            groupchat=self.group_chat,
            llm_config=get_llm_config(),
        )
        
        logger.info("AutoGen orchestrator initialized successfully")
    
    async def chat(self, user_message: str) -> str:
        """
        Process user message through AutoGen GroupChat
        
        Args:
            user_message: User's input message
            
        Returns:
            AI response from appropriate agent
        """
        try:
            with trace_agent_action(
                "OrchestratorAgent", 
                "group_chat",
                message=user_message,
                conversation_length=len(self.group_chat.messages),
                max_rounds=self.group_chat.max_round
            ):
                logger.info(f"Processing message with AutoGen: {user_message}")
                logger.info(f"Current conversation history: {len(self.group_chat.messages)} messages")
                
                try:
                    # Initiate chat with the user proxy
                    # Messages are automatically appended to group_chat.messages
                    self.user_proxy.initiate_chat(
                        self.manager,
                        message=user_message,
                        clear_history=False,  # CRITICAL: Preserve conversation history
                    )
                except StopIteration as e:
                    # Handle generator cleanup issues gracefully
                    logger.warning(f"Generator stopped unexpectedly: {e}", exc_info=True)
                    pass
                except GeneratorExit as e:
                    # Handle generator exit gracefully
                    logger.warning(f"Generator exit detected: {e}", exc_info=True)
                    pass
                except RuntimeError as e:
                    # Handle runtime errors from generator
                    if "generator" in str(e).lower():
                        logger.warning(f"Generator runtime error: {e}", exc_info=True)
                        pass
                    else:
                        raise
                
                # Extract the final response from chat history
                chat_history = self.group_chat.messages
                
                if len(chat_history) > 0:
                    # Get the last non-user message
                    for msg in reversed(chat_history):
                        if msg.get("name") != "User":
                            response = msg.get("content", "")
                            logger.info(f"AutoGen response: {response[:100]}...")
                            return response
                
                return "I apologize, but I couldn't process your request. Please try again."
            
        except Exception as e:
            logger.error(f"Error in AutoGen orchestrator: {e}", exc_info=True)
            return f"I encountered an error: {str(e)}"
    
    def clear_history(self):
        """Clear conversation history"""
        self.group_chat.messages = []
        logger.info("Cleared AutoGen conversation history")
