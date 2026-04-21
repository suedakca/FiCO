from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import List, Optional, Union

class QueryBase(BaseModel):
    user_id: str
    query_text: str

class QueryCreate(QueryBase):
    pass

class Query(QueryBase):
    id: int
    timestamp: datetime
    response: Optional['Response'] = None
    
    class Config:
        from_attributes = True

class ResponseBase(BaseModel):
    answer_text: str
    source_urls: Union[List[str], str]
    confidence_score: float
    # Compliance Evaluation Metrics
    hit_rate: float = 0.0
    faithfulness: float = 0.0
    citation_accuracy: float = 0.0

    @field_validator('source_urls', mode='before')
    @classmethod
    def validate_source_urls(cls, v):
        if isinstance(v, str):
            if not v:
                return []
            return [s.strip() for s in v.split(',') if s.strip()]
        return v

class Response(ResponseBase):
    id: Optional[int] = None
    query_id: Optional[int] = None
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
