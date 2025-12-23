from app.db.database import Base

# Import all models here for Alembic to detect them
from app.models.property import Property
from app.models.viewing import Viewing
from app.models.faq import FAQ

__all__ = ["Base", "Property", "Viewing", "FAQ"]