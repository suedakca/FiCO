from fastapi import APIRouter
from api.v1.endpoints import query, sources, feedback

api_router = APIRouter()
api_router.include_router(query.router, prefix="/query", tags=["query"])
# api_router.include_router(sources.router, prefix="/sources", tags=["sources"])
# api_router.include_router(feedback.router, prefix="/feedback", tags=["feedback"])
