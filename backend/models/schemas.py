from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class QueryBase(BaseModel):
    user_id: str
    query_text: str

class QueryCreate(QueryBase):
    pass

class Query(QueryBase):
    id: int
    timestamp: datetime
    
    class Config:
        from_attributes = True

class ResponseBase(BaseModel):
    answer_text: str
    source_urls: List[str]
    confidence_score: float

class Response(ResponseBase):
    id: int
    query_id: int
    timestamp: datetime
    
    class Config:
        from_attributes = True

class FeedbackBase(BaseModel):
    rating: int
    comments: Optional[str] = None

class FeedbackCreate(FeedbackBase):
    response_id: int

class Feedback(FeedbackBase):
    id: int
    response_id: int
    timestamp: datetime
    
    class Config:
        from_attributes = True
