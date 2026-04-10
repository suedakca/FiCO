from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from .inference import inference_engine

# 1. API Uygulaması
app = FastAPI(
    title="FiCO (Fikh Compliance Oracle)",
    description="Katılım Bankacılığı Uyum Denetçisi AI Servisi",
    version="2.0.0"
)

# 2. Veri Modelleri
class QuestionRequest(BaseModel):
    question: str

class AnswerResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    confidence: float

# 3. Endpoints
@app.get("/")
def health_check():
    return {"status": "online", "system": "FiCO Oracle v2.1"}

@app.post("/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest):
    """
    Kullanıcı sorusunu alır, RAG sürecini işletir ve 
    eğitilmiş model üzerinden uzman cevabı döner.
    """
    try:
        # Inference akışını başlat (Retrieve -> Reason -> Respond)
        result = inference_engine.generate_response(request.question)
        
        return {
            "answer": result.get("answer", "Cevap üretilemedi."),
            "sources": result.get("sources", []),
            "confidence": result.get("confidence", 0.0)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
