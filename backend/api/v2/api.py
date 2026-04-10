import json
import time
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from .inference import inference_engine

# 1. API Uygulaması (v3.1)
app = FastAPI(
    title="FiCO v3.1 (Governed Decision System)",
    description="Kurumsal Karar Motoru - Politika ve Yönetişim Denetimli",
    version="3.1.0"
)

# 2. Veri Modelleri
class QuestionRequest(BaseModel):
    question: str
    mode: Optional[str] = "strict"

class DecisionTrace(BaseModel):
    priority_used: bool
    recency_used: bool

class AnswerResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    confidence: float
    query_type: str
    mode: str
    escalated: bool
    decision_trace: DecisionTrace

# 3. Gelişmiş Denetim Günlüğü (v3.1 Audit Trace)
def log_audit_v31(data: Dict[str, Any]):
    """Karar süreçlerini detaylı olarak denetim için kayıt altına alır."""
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
    return {"status": "online", "system": "FiCO v3.1 Governed Decision System"}

@app.post("/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest):
    """v3.1 - Yönetilen Karar Motoru (Governed Decision Engine)."""
    try:
        # Karar alma sürecini başlat
        result = inference_engine.generate_response(request.question, mode=request.mode)
        
        # Detaylı Denetim İzi (Audit Trace)
        log_audit_v31({
            "query": request.question,
            "query_type": result.get("query_type"),
            "mode": result.get("mode"),
            "escalated": result.get("escalated"),
            "confidence": result.get("confidence"),
            "priority_applied": result.get("decision_trace", {}).get("priority_used"),
            "recency_adjusted": result.get("decision_trace", {}).get("recency_used"),
            "final_answer": result.get("answer")
        })
        
        return {
            "answer": result.get("answer", "Analiz tamamlanamadı."),
            "sources": result.get("sources", []),
            "confidence": result.get("confidence", 0.0),
            "query_type": result.get("query_type", "unknown"),
            "mode": result.get("mode", "strict"),
            "escalated": result.get("escalated", False),
            "decision_trace": result.get("decision_trace", {"priority_used": False, "recency_used": False})
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
