from fastapi import APIRouter

from app.models.schemas import SearchRequest
from app.search.engine import search

router = APIRouter()

@router.post("/search")
def search_documents(request: SearchRequest):
    results = search(query = request.query, top_k = request.top_k)
    return{
        "query": request.query,
        "top_k": request.top_k,
        "results": results,
    }

