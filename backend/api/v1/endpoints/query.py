import json
from typing import List
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from models import schemas, database
from services.rag_service import rag_service
from core.db import get_db

router = APIRouter()

@router.post("", response_model=schemas.Response)
async def create_query(query_in: schemas.QueryCreate, db: Session = Depends(get_db)):
    # 1. Try to save query to db (Optional)
    db_query_id = None
    try:
        db_query = database.Query(
            user_id=query_in.user_id,
            query_text=query_in.query_text
        )
        db.add(db_query)
        db.commit()
        db.refresh(db_query)
        db_query_id = db_query.id
    except Exception as e:
        db.rollback()
        print(f"⚠️ Query DB'ye kaydedilemedi: {e}")

    # 2. Call RAG Service (Mandatory)
    try:
        rag_result = await rag_service.query(query_in.query_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG Error: {str(e)}")

    # 3. Try to save response to db (Optional)
    db_response_id = None
    timestamp = None
    try:
        if db_query_id:
            db_response = database.Response(
                query_id=db_query_id,
                answer_text=rag_result["answer_text"],
                source_urls=",".join(rag_result["source_urls"]),
                confidence_score=rag_result["confidence_score"]
            )
            db.add(db_response)
            db.commit()
            db.refresh(db_response)
            db_response_id = db_response.id
            timestamp = db_response.timestamp
    except Exception as e:
        db.rollback()
        print(f"⚠️ Response DB'ye kaydedilemedi: {e}")

    # Convert to schema (Works even if DB fails)
    import datetime
    return schemas.Response(
        id=db_response_id,
        query_id=db_query_id,
        answer_text=rag_result["answer_text"],
        source_urls=rag_result["source_urls"],
        confidence_score=rag_result["confidence_score"],
        hit_rate=rag_result.get("hit_rate", 0.0),
        faithfulness=rag_result.get("faithfulness", 0.0),
        citation_accuracy=rag_result.get("citation_accuracy", 0.0),
        timestamp=timestamp or datetime.datetime.now()
    )

@router.post("/stream")
async def stream_query(query_in: schemas.QueryBase, db: Session = Depends(get_db)):
    """Anlık veri akışı (Streaming) sağlayan ve sonucu veritabanına kaydeden endpoint."""
    async def event_generator():
        full_answer = ""
        metadata = {}
        
        async for chunk in rag_service.stream_query(query_in.query_text):
            if "[METADATA]" in chunk:
                parts = chunk.split("[METADATA]")
                full_answer += parts[0]
                try:
                    metadata = json.loads(parts[1])
                except:
                    pass
            else:
                full_answer += chunk
            
            yield chunk

        # Stream bittiğinde DB'ye kaydet
        try:
            db_query = database.Query(
                user_id=query_in.user_id,
                query_text=query_in.query_text
            )
            db.add(db_query)
            db.commit()
            db.refresh(db_query)

            db_response = database.Response(
                query_id=db_query.id,
                answer_text=full_answer.strip(),
                source_urls=",".join(metadata.get("source_urls", [])),
                confidence_score=metadata.get("confidence_score", 0.9)
            )
            db.add(db_response)
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"⚠️ Stream sonucu kaydedilemedi: {e}")

    return StreamingResponse(event_generator(), media_type="text/plain")

@router.get("", response_model=List[schemas.Query])
async def get_queries(user_id: str = "demo_user", db: Session = Depends(get_db)):
    queries = db.query(database.Query).options(joinedload(database.Query.response)).filter(database.Query.user_id == user_id).order_by(database.Query.timestamp.desc()).limit(10).all()
    return queries
