import json
import time
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from .inference import inference_engine
from backend.core.feedback import feedback_loop

# 1. API Uygulaması (v3.2)
app = FastAPI(
    title="FiCO v3.2 (Trusted AI System)",
    description="Deterministik, İzlenebilir ve Güvenilir Kurumsal Karar Motoru",
    version="3.2.0"
)

# 1.1 CORS Yapılandırması
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Veri Modelleri
class QuestionRequest(BaseModel):
    question: str
    mode: Optional[str] = "production"

class FeedbackRequest(BaseModel):
    query: str
    answer: str
    feedback: str # "correct" | "incorrect"
    comment: Optional[str] = None

class AnswerResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    confidence: float
    query_type: str
    mode: str
    escalated: bool
    policy_version: str
    cache_hit: bool
    decision_trace: Dict[str, Any]

# 3. Replay-Ready Audit Trace (v3.2)
def log_audit_v32(data: Dict[str, Any]):
    """Sorgunun tam olarak tekrar oynatılabilmesi için tüm parametreleri kaydeder."""
    log_file = "./backend/data/audit.jsonl"
    with open(log_file, "a", encoding="utf-8") as f:
        log_entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            **data
        }
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

# 4. Endpoints
@app.get("/")
def health_check():
    return {"status": "online", "system": "FiCO v3.2 Trusted AI"}

@app.post("/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest):
    """v3.2 - Güvenilir Karar Motoru (Deterministic & Traceable)."""
    try:
        # Karar alma sürecini başlat
        result = inference_engine.generate_response(request.question, mode=request.mode)
        
        # v3.2 Audit Trace
        log_audit_v32({
            "query": request.question,
            "normalized_query": result.get("normalized_query"),
            "cache_key": result.get("cache_key"),
            "model_params": result.get("model_params"),
            "policy_versions_used": result.get("policy_versions_used", []),
            "confidence": result.get("confidence"),
            "escalated": result.get("escalated"),
            "final_answer": result.get("answer")
        })
        
        return {
            "answer": result.get("answer", "Analiz tamamlanamadı."),
            "sources": result.get("sources", []),
            "confidence": result.get("confidence", 0.0),
            "query_type": result.get("query_type", "unknown"),
            "mode": result.get("mode", "production"),
            "escalated": result.get("escalated", False),
            "policy_version": result.get("policy_versions_used", ["v1.0"])[0],
            "cache_hit": result.get("cache_hit", False),
            "decision_trace": result.get("decision_trace", {})
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/feedback")
async def submit_feedback(request: FeedbackRequest):
    """Kullanıcı geri bildirimlerini toplar ve öz-iyileştirme için kaydeder."""
    try:
        feedback_loop.record_feedback(request.model_dump())
        return {"status": "success", "message": "Geri bildiriminiz kaydedilmiştir."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
