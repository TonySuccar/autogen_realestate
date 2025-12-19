import os
from openai import OpenAI
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.faq import FAQ
from app.config.settings import get_settings
from app.middleware.logging import logger

settings = get_settings()

def generate_faq_embeddings():
    """
    Generate embeddings for all FAQs using OpenAI API and store in DB.
    Deletes old embeddings and regenerates fresh ones.
    """
    logger.info("Starting FAQ embedding generation...")

    # Initialize OpenAI client
    client = OpenAI(api_key=settings.openai_api_key)

    db: Session = SessionLocal()

    try:
        faqs = db.query(FAQ).all()
        logger.info(f"Found {len(faqs)} FAQs in the database.")
        
        # Delete old embeddings first
        embeddings_deleted = 0
        for faq in faqs:
            if faq.embedding:
                faq.embedding = None
                embeddings_deleted += 1
        
        if embeddings_deleted > 0:
            db.commit()
            logger.info(f"Deleted {embeddings_deleted} old embeddings.")

        # Generate new embeddings for all FAQs
        for faq in faqs:
            text_to_embed = faq.question + " " + faq.answer
            response = client.embeddings.create(
                model="text-embedding-3-small",
                input=text_to_embed
            )

            # Extract the embedding values
            embedding_values = response.data[0].embedding
            
            # Store embedding in DB
            faq.embedding = embedding_values
            db.add(faq)
            logger.info(f"Generated embedding for FAQ {faq.id}: {faq.question[:50]}...")

        db.commit()
        logger.info(f"Successfully generated {len(faqs)} new FAQ embeddings!")

    except Exception as e:
        db.rollback()
        logger.error(f"Error generating embeddings: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    generate_faq_embeddings()
