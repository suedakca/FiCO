import re
from typing import List, Dict, Any
from backend.oracle.rag import retrieve_context
from backend.oracle.classifier import query_classifier
from backend.oracle.governance import governance_engine
from backend.core.cache import query_cache

class FiCOInferenceV32:
    """FiCO v3.2 - Trusted AI System Inference Motoru (Deterministic & Governed)."""
    
    def __init__(self, threshold: float = 0.7):
        self.threshold = threshold
        # Deterministik parametreler
        self.model_params = {
            "temperature": 0,
            "top_p": 0.9
        }

    def normalize_query(self, query: str) -> str:
        """Sorguyu standartlaştırır ve determinizm için hazırlar."""
        query = query.lower().strip()
        # Gürültü ve fazla boşluk temizleme
        query = re.sub(r'[^\w\s\?]', '', query)
        query = " ".join(query.split())
        return query

    def generate_response(self, question: str, mode: str = "production") -> Dict[str, Any]:
        """v3.2 Akışı: Normalize -> Cache Check -> Governed Search -> Twin-Inference -> Store."""
        
        # 1. Sorgu Normalizasyonu ve Cache Anahtarı
        normalized_query = self.normalize_query(question)
        cache_key = query_cache.generate_key(normalized_query)
        
        # 2. Önbellek Kontrolü (Determinism Layer)
        cached_res = query_cache.get(cache_key)
        if cached_res and mode == "production":
            cached_res["cache_hit"] = True
            return cached_res

        # 3. Akıllı Karar Akışı
        result = self._execute_inference(normalized_query, mode)
        
        # 4. Tutarlılık Doğrulaması (Twin-Inference - Sadece Production Modunda)
        if mode == "production" and not result.get("escalated"):
            twin_result = self._execute_inference(normalized_query, mode)
            if twin_result["answer"] != result["answer"]:
                # Tutarsızlık durumunda eskalasyon
                result["escalated"] = True
                result["answer"] = "This matter should be escalated due to internal consistency mismatch. (Sistem tutarsızlığı tespit edilmiştir.)"

        # 5. Önbelleğe Kaydet
        result["cache_hit"] = False
        result["normalized_query"] = normalized_query
        result["cache_key"] = cache_key
        result["model_params"] = self.model_params
        
        query_cache.set(cache_key, result)
        return result

    def _execute_inference(self, query: str, mode: str) -> Dict[str, Any]:
        """Alt seviye muhakeme icrası."""
        query_type = query_classifier.classify(query)
        context_docs = retrieve_context(query)
        
        # Confidence v2 (+ Priority + Recency)
        final_confidence = 0.0
        if context_docs:
            scores = [( (min(1.0, (d.get("score", 0)+5)/10) * 0.5) + (d.get("priority_score", 0.25) * 0.3) + (d.get("recency_score", 0.5) * 0.2) ) for d in context_docs]
            final_confidence = round(max(scores), 4)

        is_escalated = governance_engine.should_escalate(query, context_docs, final_confidence, query_type)
        
        if is_escalated:
            return {
                "answer": "This matter should be escalated to the Sharia Advisory Board. (Güven eşiği altı veya kritik risk.)",
                "sources": context_docs,
                "confidence": final_confidence,
                "query_type": query_type,
                "mode": mode,
                "escalated": True,
                "policy_versions_used": [d.get("metadata", {}).get("version", "v1.0") for d in context_docs]
            }

        # Mock Answer
        answer = "HÜKÜM:\nBanka v3.0 politikası çerçevesinde işlem UYGUNDUR.\n\nGEREKÇE:\nİç mevzuat önceliği ve günellik kriterleri korunmuştur."
        
        return {
            "answer": answer,
            "sources": context_docs[:2],
            "confidence": final_confidence,
            "query_type": query_type,
            "mode": mode,
            "escalated": False,
            "policy_versions_used": [d.get("metadata", {}).get("version", "v1.0") for d in context_docs[:2]]
        }

# Singleton instance
inference_engine = FiCOInferenceV32()
