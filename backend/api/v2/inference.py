from typing import List, Dict, Any
import numpy as np
from backend.oracle.rag import retrieve_context, rag_engine
from backend.oracle.classifier import query_classifier

class FiCOInferenceV3:
    """FiCO v3.0 - Enterprise Explainable AI Inference Motoru."""
    
    def __init__(self, threshold: float = 0.7):
        self.threshold = threshold
        self.prompts = {
            "compliance_decision": "TALİMAT: Kesin ve kuralcı bir ton kullan. Sadece dökümanlardaki hükümlere odaklan. Spekülasyon yapma.",
            "comparison": "TALİMAT: Kurallar arasındaki benzerlik ve farkları madde madde açıkla. Mukayeseli bir analiz sun.",
            "edge_case": "TALİMAT: İstisnai durumları ve koşulları (eğer, ise) vurgulayarak analiz et. Operasyonel riskleri belirt.",
            "definition": "TALİMAT: Terimin mevzuat sözlüğündeki karşılığını ve kapsamını açıkla.",
            "general_inquiry": "TALİMAT: Profesyonel bir üslupla genel mevzuat bilgilendirmesi yap."
        }

    def generate_response(self, question: str) -> Dict[str, Any]:
        """v3.0 Akışı: Classify -> Retrieve -> Reason -> Map Evidence."""
        
        # 1. Sorgu Sınıflandırma
        query_type = query_classifier.classify(question)
        
        # 2. Gelişmiş Arama (Reranked & Deduplicated)
        context_docs = retrieve_context(question)
        
        # 3. Confidence Filtering
        filtered_context = [doc for doc in context_docs if doc.get("score", 0) >= self.threshold]
        
        # 4. Dinamik Güven Skoru (max_sim * coverage)
        confidence = 0.0
        if filtered_context:
            max_sim = max(d["score"] for d in filtered_context)
            coverage_factor = min(1.0, len(filtered_context) / 3.0) # 3 döküman tam kapsam sayılır
            confidence = round(max_sim * coverage_factor, 4)

        # 5. Reddetme Mantığı
        if not filtered_context:
            return {
                "answer": "Bu konuda mevcut veri setinde açık bir hüküm bulunamamıştır.",
                "sources": [],
                "confidence": 0.0,
                "query_type": query_type,
                "evidence": []
            }

        # 6. Dinamik Prompt Seçimi
        specialized_instruction = self.prompts.get(query_type, self.prompts["general_inquiry"])
        
        # 7. Bağlam Hazırlığı
        context_text = ""
        for i, doc in enumerate(filtered_context):
            context_text += f"[KAYNAK {i+1}]: {doc['content']} (Referans: {doc['metadata'].get('exact_citation','')})\n\n"

        # 8. Mock Answer (Gerçekte LLM tarafından üretilecek)
        answer = "HÜKÜM:\nİlgili katılım bankacılığı mevzuatı uyarınca işlem caizdir.\n\nGEREKÇE:\nİşlemde risk paylaşımı yapıldığı görülmektedir."
        
        # 9. Kanıt Eşleme (Evidence Mapping)
        evidence = self._map_evidence(answer, filtered_context)

        return {
            "answer": answer,
            "sources": filtered_context,
            "confidence": confidence,
            "query_type": query_type,
            "evidence": evidence
        }

    def _map_evidence(self, answer: str, context: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Cevaptaki iddiaları dökümanlarla eşleştirir (Basit semantik eşleme)."""
        evidence_list = []
        sentences = answer.split(".")
        
        for sent in sentences:
            if len(sent.strip()) < 10: continue
            
            # Her cümle için en yakın dökümanı bul (Simüle ediliyor)
            # v3.0'da burada cümle seviyesinde embedding karşılaştırması yapılır.
            best_match = context[0] 
            evidence_list.append({
                "rule_id": best_match.get("id"),
                "text": sent.strip(),
                "source": best_match["metadata"].get("exact_citation"),
                "similarity": best_match.get("score")
            })
        return evidence_list

# Singleton instance
inference_engine = FiCOInferenceV3()
