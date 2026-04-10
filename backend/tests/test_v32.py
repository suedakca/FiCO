import pytest
from fastapi.testclient import TestClient
from backend.api.v2.api import app
from backend.oracle.rag import retrieve_context
from backend.oracle.classifier import query_classifier
from backend.oracle.governance import governance_engine
from backend.api.v2.inference import inference_engine

client = TestClient(app)

def test_query_normalization():
    """Sorgu normalizasyonunun beklenen şekilde çalışıp çalışmadığını test eder."""
    raw_query = "  Mudaraba  NEDİR?  "
    normalized = inference_engine.normalize_query(raw_query)
    assert normalized == "mudaraba nedir"

def test_query_classifier():
    """Sorgu tipinin doğru kategorize edildiğini test eder."""
    assert query_classifier.classify("Mudaraba caiz mi?") == "compliance_decision"
    assert query_classifier.classify("Murabaha nedir?") == "definition"
    assert query_classifier.classify("Farkı nedir?") == "comparison"

def test_governance_priority():
    """Politika hiyerarşisinin doğru skorlandığını test eder."""
    # Kuveyt Türk İç Fetva -> 3 (3/4 = 0.75)
    # AAOIFI -> 1 (1/4 = 0.25)
    p_high = governance_engine.get_priority_score("Kuveyt Türk İç Fetva")
    p_low = governance_engine.get_priority_score("AAOIFI Standard")
    assert p_high == 0.75
    assert p_low == 0.25

def test_api_reproducibility():
    """Aynı sorgunun aynı hash ve sonucu döndürdüğünü (determinism) test eder."""
    q = "Mudaraba nedir?"
    res1 = client.post("/ask", json={"question": q, "mode": "production"}).json()
    res2 = client.post("/ask", json={"question": q, "mode": "production"}).json()
    
    assert res1["answer"] == res2["answer"]
    # İkinci deneme cache hit olmalı (Cache hit field AnswerResponse içinde var)
    assert res2["cache_hit"] is True

def test_api_feedback():
    """Geri bildirim endpoint'inin çalıştığını test eder."""
    response = client.post("/feedback", json={
        "query": "test query",
        "answer": "test answer",
        "feedback": "correct"
    })
    assert response.status_code == 200
    assert response.json()["status"] == "success"

@pytest.mark.parametrize("query", [
    "Mudaraba sözleşmesinde zarar kim karşılar?",
    "Vadeli döviz işlemi caiz midir?"
])
def test_rag_retrieval(query):
    """RAG hattının döküman getirdiğini test eder."""
    docs = retrieve_context(query)
    assert len(docs) > 0
    assert "content" in docs[0]
