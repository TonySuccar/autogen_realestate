"""
Database seeding script
Creates sample data for development and testing
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.db.database import SessionLocal, engine, Base
from app.models.user import User
from app.models.property import Property
from app.models.viewing import Viewing, ViewingStatus
from app.models.faq import FAQ
from app.middleware.logging import logger
import random


def clear_all_data(db: Session):
    """Delete all existing data from all tables"""
    logger.info("Clearing all existing data...")
    
    try:
        # Delete in reverse order of dependencies
        db.query(Viewing).delete()
        db.query(Property).delete()
        db.query(User).delete()
        db.query(FAQ).delete()
        db.commit()
        logger.info("All existing data cleared")
    except Exception as e:
        db.rollback()
        logger.error(f"Error clearing data: {e}")
        raise


def create_users(db: Session, count: int = 10):
    """Create sample users"""
    logger.info(f"Creating {count} users...")
    
    users = []
    names = ["John Smith", "Sarah Johnson", "Michael Brown", "Emily Davis", 
             "David Wilson", "Emma Martinez", "James Anderson", "Olivia Taylor",
             "Robert Thomas", "Sophia Garcia"]
    
    for i in range(count):
        user = User(
            name=names[i],
            email=f"{names[i].lower().replace(' ', '.')}@example.com",
        )
        users.append(user)
        db.add(user)
    
    db.commit()
    logger.info(f"Created {count} users")
    return users


def create_properties(db: Session, users: list, count: int = 10):
    """Create sample properties"""
    logger.info(f"Creating {count} properties...")
    
    properties = []
    cities = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", 
              "Philadelphia", "San Antonio", "San Diego", "Dallas", "Austin"]
    
    titles = [
        "Luxury Downtown Apartment",
        "Spacious Family Home",
        "Modern City Condo",
        "Charming Suburban House",
        "Beachfront Villa",
        "Cozy Studio Apartment",
        "Executive Penthouse",
        "Renovated Townhouse",
        "Garden View Apartment",
        "Contemporary Loft"
    ]
    
    descriptions = [
        "Beautiful property with stunning views and modern amenities.",
        "Perfect for families, featuring a large backyard and updated kitchen.",
        "Located in the heart of downtown with easy access to transportation.",
        "Quiet neighborhood with excellent schools nearby.",
        "Wake up to ocean views in this luxurious property.",
        "Ideal starter home with low maintenance costs.",
        "Top floor unit with panoramic city views.",
        "Completely remodeled with high-end finishes.",
        "Peaceful setting with garden access and natural light.",
        "Open concept design with exposed brick and high ceilings."
    ]
    
    for i in range(count):
        property = Property(
            title=titles[i],
            description=descriptions[i],
            city=cities[i],
            price=random.uniform(150000, 2000000),
            size_sqft=random.uniform(500, 3500),
            owner_id=users[i].id
        )
        properties.append(property)
        db.add(property)
    
    db.commit()
    logger.info(f"Created {count} properties")
    return properties


def create_viewings(db: Session, users: list, properties: list, count: int = 10):
    """Create sample viewings"""
    logger.info(f"Creating {count} viewings...")
    
    viewings = []
    
    # Create viewings for the next 2 weeks and past week
    base_date = datetime.now()
    
    for i in range(count):
        # Random date between -7 and +14 days
        days_offset = random.randint(-7, 14)
        scheduled_at = base_date + timedelta(days=days_offset, hours=random.randint(9, 17))
        
        # Determine status based on date
        if days_offset < 0:
            # Past viewings
            status = random.choice([ViewingStatus.COMPLETED, ViewingStatus.CANCELLED])
        else:
            # Future viewings
            status = random.choice([ViewingStatus.SCHEDULED, ViewingStatus.CANCELLED])
        
        # Select random property
        property = random.choice(properties)
        
        viewing = Viewing(
            property_id=property.id,
            scheduled_at=scheduled_at,
            status=status
        )
        viewings.append(viewing)
        db.add(viewing)
    
    db.commit()
    logger.info(f"Created {count} viewings")
    return viewings


def create_faqs(db: Session, count: int = 20):
    """Create sample FAQs"""
    logger.info(f"Creating {count} FAQs...")
    
    faq_data = [
        {
            "question": "What documents do I need to buy a property?",
            "answer": "To buy a property, you typically need: proof of identity (passport or driver's license), proof of address, bank statements (3-6 months), proof of income, mortgage agreement in principle, and details of your solicitor.",
            "tags": ["buying", "documents", "requirements"]
        },
        {
            "question": "How long does the home buying process take?",
            "answer": "The home buying process typically takes 8-12 weeks from offer acceptance to completion. This can vary depending on the property chain, mortgage approval speed, and how quickly searches and surveys are completed.",
            "tags": ["buying", "timeline", "process"]
        },
        {
            "question": "What is a mortgage pre-approval?",
            "answer": "A mortgage pre-approval is a lender's conditional commitment to loan you a specific amount. It gives you a clear budget and shows sellers you're a serious buyer. Pre-approval typically lasts 60-90 days.",
            "tags": ["mortgage", "finance", "buying"]
        },
        {
            "question": "What are closing costs?",
            "answer": "Closing costs are fees paid at the end of a real estate transaction. They typically include solicitor fees, survey costs, mortgage arrangement fees, stamp duty, and search fees. Expect to pay 3-5% of the property price.",
            "tags": ["costs", "fees", "buying"]
        },
        {
            "question": "Should I get a home inspection?",
            "answer": "Yes, a home inspection is highly recommended. A professional survey can identify structural issues, electrical problems, plumbing concerns, and other defects that could cost thousands to repair.",
            "tags": ["inspection", "survey", "buying"]
        },
        {
            "question": "What is stamp duty and who pays it?",
            "answer": "Stamp Duty Land Tax is a tax paid by the buyer on properties over a certain threshold. First-time buyers get relief on properties up to £425,000. Rates increase with property value.",
            "tags": ["tax", "costs", "buying"]
        },
        {
            "question": "How much deposit do I need?",
            "answer": "Most lenders require a minimum deposit of 5-10% of the property price. However, a larger deposit (15-20%) typically gets you better mortgage rates. First-time buyers may access special schemes requiring smaller deposits.",
            "tags": ["deposit", "mortgage", "buying"]
        },
        {
            "question": "What is gazumping?",
            "answer": "Gazumping occurs when a seller accepts a higher offer from another buyer after already accepting your offer but before contracts are exchanged. While legal, it's considered unethical in the property market.",
            "tags": ["buying", "process", "terms"]
        },
        {
            "question": "How do I determine the right asking price for my property?",
            "answer": "Get professional valuations from 2-3 estate agents, research recent sales of similar properties in your area, consider current market conditions, and factor in your property's unique features and condition.",
            "tags": ["selling", "pricing", "valuation"]
        },
        {
            "question": "What is conveyancing?",
            "answer": "Conveyancing is the legal process of transferring property ownership from seller to buyer. It includes conducting searches, reviewing contracts, handling the exchange of contracts, and managing the transfer of funds.",
            "tags": ["legal", "process", "buying", "selling"]
        },
        {
            "question": "Can I view a property more than once?",
            "answer": "Yes, you can request additional viewings. It's recommended to view at different times of day, bring family members or a surveyor on second viewings, and check the neighborhood thoroughly before making an offer.",
            "tags": ["viewing", "process"]
        },
        {
            "question": "What is the difference between freehold and leasehold?",
            "answer": "Freehold means you own the property and the land it sits on outright. Leasehold means you own the property for a fixed period and may pay ground rent and service charges to the freeholder.",
            "tags": ["ownership", "legal", "terms"]
        },
        {
            "question": "How do property chains work?",
            "answer": "A property chain occurs when multiple transactions are linked - your purchase depends on the seller buying another property, which may depend on another sale. Chains can delay completions and sometimes collapse.",
            "tags": ["buying", "selling", "process"]
        },
        {
            "question": "What should I look for during a property viewing?",
            "answer": "Check for: structural issues (cracks, damp), water pressure, heating system, electrical outlets, storage space, natural light, noise levels, mobile signal, parking, and the general condition of fixtures and fittings.",
            "tags": ["viewing", "inspection", "buying"]
        },
        {
            "question": "Are property prices negotiable?",
            "answer": "Yes, asking prices are usually negotiable. Research comparable sales, consider how long the property has been on market, factor in any issues found during surveys, and be prepared to justify your offer.",
            "tags": ["negotiation", "pricing", "buying"]
        },
        {
            "question": "What is an Energy Performance Certificate (EPC)?",
            "answer": "An EPC shows how energy-efficient a property is, rated from A (most efficient) to G (least efficient). Sellers must provide an EPC valid for 10 years before marketing their property.",
            "tags": ["energy", "certificates", "requirements"]
        },
        {
            "question": "Should I use an estate agent or sell privately?",
            "answer": "Estate agents provide market expertise, professional marketing, viewings management, and negotiation support. Private sales save on fees (typically 1-3%) but require more effort and may achieve lower prices.",
            "tags": ["selling", "estate agents", "options"]
        },
        {
            "question": "What happens on completion day?",
            "answer": "On completion day, your solicitor transfers the remaining funds to the seller's solicitor. Once confirmed, you receive the keys, the property legally becomes yours, and you can move in.",
            "tags": ["completion", "process", "buying"]
        },
        {
            "question": "Can I pull out of a property purchase?",
            "answer": "You can withdraw from a purchase before exchanging contracts without penalty. After exchange, you're legally bound and withdrawing means losing your deposit and potentially facing legal action.",
            "tags": ["buying", "legal", "contracts"]
        },
        {
            "question": "What insurance do I need when buying a property?",
            "answer": "You'll need buildings insurance (required by mortgage lenders) from the exchange date. Consider also getting contents insurance, life insurance, and mortgage payment protection insurance.",
            "tags": ["insurance", "protection", "requirements"]
        }
    ]
    
    faqs = []
    for i in range(min(count, len(faq_data))):
        faq = FAQ(
            question=faq_data[i]["question"],
            answer=faq_data[i]["answer"],
            tags=faq_data[i]["tags"]
        )
        faqs.append(faq)
        db.add(faq)
    
    db.commit()
    logger.info(f"Created {len(faqs)} FAQs")
    return faqs


def seed_database():
    """Main seeding function"""
    logger.info("Starting database seeding...")
    
    # Create tables
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Tables created")
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Clear existing data
        clear_all_data(db)
        
        # Create seed data
        users = create_users(db, count=10)
        properties = create_properties(db, users, count=10)
        viewings = create_viewings(db, users, properties, count=10)
        faqs = create_faqs(db, count=20)
        
        logger.info("=" * 60)
        logger.info("Database seeding completed successfully!")
        logger.info(f"   - Users: {len(users)}")
        logger.info(f"   - Properties: {len(properties)}")
        logger.info(f"   - Viewings: {len(viewings)}")
        logger.info(f"   - FAQs: {len(faqs)}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
