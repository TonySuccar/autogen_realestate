from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any
from app.db.database import get_db
from app.services.faq_service import search_faq_rag

router = APIRouter(prefix="/faq", tags=["FAQ"])


class FAQSearchRequest(BaseModel):
    query: str
    top_k: int = 3


class FAQSearchResponse(BaseModel):
    results: List[Dict[str, Any]]


@router.post("/search", response_model=FAQSearchResponse)
async def search_faq(req: FAQSearchRequest, db: Session = Depends(get_db)):
    """
    Search FAQ database using semantic similarity.
    
    - **query**: The question to search for
    - **top_k**: Number of top results to return (default: 3)
    """
    try:
        results = search_faq_rag(db, req.query, req.top_k)
        return {"results": results}
    except Exception as e:
        return {"results": [], "error": str(e)}
