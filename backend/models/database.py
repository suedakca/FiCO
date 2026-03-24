from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Query(Base):
    __tablename__ = "queries"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    query_text = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    response = relationship("Response", back_populates="query", uselist=False)

class Response(Base):
    __tablename__ = "responses"
    
    id = Column(Integer, primary_key=True, index=True)
    query_id = Column(Integer, ForeignKey("queries.id"))
    answer_text = Column(Text)
    source_urls = Column(Text)  # Stored as comma-separated or JSON string
    confidence_score = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    query = relationship("Query", back_populates="response")
    feedback = relationship("Feedback", back_populates="response", uselist=False)

class Feedback(Base):
    __tablename__ = "feedbacks"
    
    id = Column(Integer, primary_key=True, index=True)
    response_id = Column(Integer, ForeignKey("responses.id"))
    rating = Column(Integer)  # 1-5
    comments = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    response = relationship("Response", back_populates="feedback")
