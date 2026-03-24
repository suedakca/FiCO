from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class FeedbackRequest(BaseModel):
    response_id: str
    rating: int
    comments: str = None

@router.post("/")
async def create_feedback(feedback: FeedbackRequest):
    return {"status": "success", "message": "Geri bildiriminiz için teşekkürler."}
