from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.models.faq import FAQ
from app.middleware.logging import logger
import numpy as np


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Calculate cosine similarity between two vectors"""
    a = np.array(a)
    b = np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def search_faq_rag(db: Session, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """
    Search FAQs using RAG (Retrieval Augmented Generation)
    Uses semantic search with embeddings to find most relevant FAQs
    
    Args:
        db: Database session
        query: User's question
        top_k: Number of top results to return (default: 3)
        
    Returns:
        List of FAQ dictionaries with similarity scores
    """
    try:
        from openai import OpenAI
        from app.config.settings import get_settings
        
        settings = get_settings()
        client = OpenAI(api_key=settings.openai_api_key)
        
        # Generate embedding for the query using OpenAI
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=query
        )
        query_embedding = response.data[0].embedding
        
        # Get all FAQs with embeddings
        faqs = db.query(FAQ).filter(FAQ.embedding.isnot(None)).all()
        
        if not faqs:
            return []
        
        # Calculate similarity scores
        scored = [
            (faq, cosine_similarity(query_embedding, faq.embedding))
            for faq in faqs
        ]
        
        # Sort by similarity (highest first)
        scored.sort(key=lambda x: x[1], reverse=True)
        
        # Return top_k results
        results = []
        for faq, score in scored[:top_k]:
            results.append({
                "id": faq.id,
                "question": faq.question,
                "answer": faq.answer,
                "tags": faq.tags,
                "similarity_score": float(score)
            })
        
        return results
        
    except Exception as e:
        logger.error(f"Error in search_faq_rag: {e}")
        return []


def list_faqs(db: Session) -> List[Dict[str, Any]]:
    """
    List all FAQs
    
    Args:
        db: Database session
        
    Returns:
        List of FAQ dictionaries
    """
    try:
        faqs = db.query(FAQ).all()
        
        return [
            {
                "id": faq.id,
                "question": faq.question,
                "answer": faq.answer,
                "tags": faq.tags,
            }
            for faq in faqs
        ]
    except Exception as e:
        logger.error(f"Error listing FAQs: {e}")
        raise
