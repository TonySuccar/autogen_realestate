"""
AutoGen-based FAQ Agent
"""
from autogen import ConversableAgent
from sqlalchemy.orm import Session
from typing import Annotated
from app.services.faq_service import search_faq_rag
from app.agents.autogen_config import get_llm_config, get_agent_system_messages
from app.middleware.logging import logger
from app.observability.phoenix_tracer import trace_agent_action


def search_faq_database(db: Session, query: str, top_k: int = 3) -> str:
    """
    Search the FAQ database using semantic search
    
    Args:
        db: Database session
        query: User's question
        top_k: Number of results to return
        
    Returns:
        Formatted FAQ answers
    """
    try:
        with trace_agent_action(
            "FAQAgent",
            "rag_semantic_search",
            query=query,
            top_k=top_k,
            search_type="RAG"
        ):
            results = search_faq_rag(db, query, top_k=top_k)
            
            if not results:
                return "I couldn't find specific information about that in our FAQ database, but I'm happy to provide general guidance! What would you like to know?"
            
            response = f"📚 **Here's what I found:**\n\n"
            
            for idx, result in enumerate(results, 1):
                response += f"**Q: {result['question']}**\n"
                response += f"A: {result['answer']}\n"
                
                # Show similarity score
                similarity_pct = result.get('similarity_score', 0) * 100
                response += f"_Relevance: {similarity_pct:.1f}%_\n"
                
                if result.get('tags'):
                    response += f"_Tags: {', '.join(result['tags'])}_\n"
                
                response += "\n"
            
            response += "\n💡 **Still have questions?** Feel free to ask for more details!"
            
            logger.info(f"Found {len(results)} FAQ matches for query: {query}")
            return response
        
    except Exception as e:
        logger.error(f"Error searching FAQs: {e}")
        return "I had trouble searching the FAQ database. Let me try to help you anyway - what's your question?"


class FAQAgentAutogen:
    """
    AutoGen-based FAQ/Q&A Agent
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.system_message = get_agent_system_messages()["faq_agent"]
        
        # Create AutoGen conversable agent
        self.agent = ConversableAgent(
            name="FAQAgent",
            system_message=self.system_message,
            llm_config=get_llm_config(),
            human_input_mode="NEVER",
            max_consecutive_auto_reply=2,  # Reduced for faster responses
        )
        
        # Create wrapper function with Annotated type hints - MUST capture self.db in closure
        def search_faq_wrapper(
            query: Annotated[str, "The user's question about real estate (e.g., 'What documents do I need to buy a house?')"],
            top_k: Annotated[int, "Number of FAQ results to return (default 3)"] = 3
        ) -> str:
            logger.info(f"FAQ tool called with query: {query}, top_k: {top_k}")
            try:
                result = search_faq_database(self.db, query, top_k)
                logger.info(f"FAQ search successful, returning {len(result)} characters")
                return result
            except Exception as e:
                logger.error(f"FAQ tool error: {e}", exc_info=True)
                return f"Error searching FAQ: {str(e)}"
        
        # Register tool using new AutoGen API
        self.agent.register_for_llm(
            name="search_faq_database",
            description="MANDATORY: Search the FAQ database for EVERY question. Returns accurate answers from the knowledge base with similarity scores. You MUST call this before answering any question."
        )(search_faq_wrapper)
        
        # Register for execution
        self.agent.register_for_execution(
            name="search_faq_database"
        )(search_faq_wrapper)
