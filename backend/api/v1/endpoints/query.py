from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from models import schemas, database
from services.rag_service import rag_service
from core.db import get_db

router = APIRouter()

@router.post("/", response_model=schemas.Response)
async def create_query(query_in: schemas.QueryCreate, db: Session = Depends(get_db)):
    # 1. Save query to db
    db_query = database.Query(
        user_id=query_in.user_id,
        query_text=query_in.query_text
    )
    db.add(db_query)
    db.commit()
    db.refresh(db_query)

    # 2. Call RAG Service
    try:
        rag_result = await rag_service.query(query_in.query_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG Error: {str(e)}")

    # 3. Save response to db
    db_response = database.Response(
        query_id=db_query.id,
        answer_text=rag_result["answer_text"],
        source_urls=",".join(rag_result["source_urls"]),
        confidence_score=rag_result["confidence_score"]
    )
    db.add(db_response)
    db.commit()
    db.refresh(db_response)

    # Convert to schema
    return schemas.Response(
        id=db_response.id,
        query_id=db_response.query_id,
        answer_text=db_response.answer_text,
        source_urls=rag_result["source_urls"],
        confidence_score=db_response.confidence_score,
        timestamp=db_response.timestamp
    )
