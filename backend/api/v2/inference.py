from typing import List, Dict, Any
import numpy as np
from backend.oracle.rag import retrieve_context
from backend.oracle.classifier import query_classifier
from backend.oracle.governance import governance_engine

class FiCOInferenceV31:
    """FiCO v3.1 - Governed Decision System Inference Motoru."""
    
    def __init__(self, threshold: float = 0.7):
        self.threshold = threshold
        self.prompts = {
            "strict": "MOD: STRICT (KESİN). Spekülasyon yapma. Sadece dökümanlardaki net hükümlere odaklan. Belirsizlik varsa eskalasyon öner.",
            "advisory": "MOD: ADVISORY (TAVSİYE). Kavramsal açıklamalar yapabilirsin. Bağlamsal muhakeme sun ve tavsiyelerde bulun.",
            "compliance_decision": "GÖREV: Kritik Uyum Kararı. Kurallar arası hiyerarşiye sadık kal.",
            "general": "GÖREV: Genel Bilgilendirme."
        }

    def generate_response(self, question: str, mode: str = "strict") -> Dict[str, Any]:
        """v3.1 Akışı: Classify -> Retrieve (Governed) -> Score -> Escalate -> Respond."""
        
        # 1. Sorgu Sınıflandırma
        query_type = query_classifier.classify(question)
        
        # 2. Yönetişim Destekli Arama (Reranked + Priority Filtered)
        context_docs = retrieve_context(question)
        
        # 3. Gelişmiş Karar Skorlaması (Confidence v2)
        # Confidence = (sim * 0.5) + (priority * 0.3) + (recency * 0.2)
        final_confidence = 0.0
        decision_trace = {"priority_used": True, "recency_used": True}
        
        if context_docs:
            scores = []
            for doc in context_docs:
                # rerank_score logit olabilir, 0-1 aralığına normalize edelim (basitçe 0.8 varsayalım)
                # Gerçekte CrossEncoder çıktıları [-10, 10] arası olabilir, burada 0-1 varsayıyoruz.
                sim = min(1.0, (doc.get("score", 0) + 5) / 10) if doc.get("score", 0) > 0 else 0.5
                priority = doc.get("priority_score", 0.25)
                recency = doc.get("recency_score", 0.5)
                
                doc_conf = (sim * 0.5) + (priority * 0.3) + (recency * 0.2)
                scores.append(doc_conf)
            final_confidence = round(max(scores), 4) if scores else 0.0

        # 4. İnsan Eskalasyonu Mantığı (Escalation)
        is_escalated = governance_engine.should_escalate(question, context_docs, final_confidence, query_type)
        
        if is_escalated:
            return {
                "answer": "This matter should be escalated to the Sharia Advisory Board for expert review. (Mevcut verilerle kesin bir hükme varılamamış veya yüksek riskli bir çelişki tespit edilmiştir.)",
                "sources": context_docs,
                "confidence": final_confidence,
                "query_type": query_type,
                "mode": mode,
                "escalated": True,
                "decision_trace": decision_trace
            }

        # 5. Dinamik Prompt ve Yanıt Oluşturma
        mode_instruction = self.prompts.get(mode, self.prompts["strict"])
        type_instruction = self.prompts.get(query_type, self.prompts["general"])
        
        # 6. Mock Response Logic (v3.1 Kurumsal Karar formatı)
        answer = "HÜKÜM:\nBanka politikaları ve mevzuat önceliği çerçevesinde işlem UYGUNDUR.\n\nGEREKÇE:\nİç politikalar (Priority 4) AAOIFI kurallarına nazaran daha güncel (2025) kriterler sunmaktadır."

        return {
            "answer": answer,
            "sources": context_docs[:2], # En iyi 2 kaynak
            "confidence": final_confidence,
            "query_type": query_type,
            "mode": mode,
            "escalated": False,
            "decision_trace": decision_trace
        }

# Singleton instance
inference_engine = FiCOInferenceV31()
