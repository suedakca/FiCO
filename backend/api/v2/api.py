import json
import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from .inference import inference_engine

# 1. API Uygulaması
app = FastAPI(
    title="FiCO v3.0 (Enterprise Explainable AI)",
    description="Denetlenebilir ve Açıklanabilir Katılım Bankacılığı Uyum Analisti",
    version="3.0.0"
)

# 2. Veri Modelleri
class QuestionRequest(BaseModel):
    question: str

class EvidenceItem(BaseModel):
    rule_id: str
    text: str
    source: str
    similarity: float

class AnswerResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    confidence: float
    query_type: str
    evidence: List[EvidenceItem]

# 3. Denetim Günlüğü (Audit Logger)
def log_audit(data: Dict[str, Any]):
    """Her sorguyu denetim için kayıt altına alır."""
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
    return {"status": "online", "system": "FiCO v3.0 Enterprise"}

@app.post("/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest):
    """v3.0 - Açıklanabilir ve Denetlenebilir Soru-Cevap Servisi."""
    try:
        # Analiz sürecini başlat
        result = inference_engine.generate_response(request.question)
        
        # Denetim Kaydı Oluştur
        log_audit({
            "query": request.question,
            "answer": result.get("answer"),
            "confidence": result.get("confidence"),
            "query_type": result.get("query_type"),
            "source_ids": [s.get("id") for s in result.get("sources", [])]
        })
        
        return {
            "answer": result.get("answer", "Cevap üretilemedi."),
            "sources": result.get("sources", []),
            "confidence": result.get("confidence", 0.0),
            "query_type": result.get("query_type", "unknown"),
            "evidence": result.get("evidence", [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
