from typing import List, Dict, Any
from backend.oracle.rag import retrieve_context

class FiCOInference:
    """FiCO (Fikh Compliance Oracle) Üretim Seviyesi Inference Motoru."""
    
    def __init__(self, model_handler=None, threshold: float = 0.7):
        self.threshold = threshold
        self.system_prompt = """Sen uzman bir 'Katılım Bankacılığı Uyum Analisti' (FiCO) ajansısın.
GÖREVİN: Kullanıcı sorularına mevzuat bağlamı üzerinden cevap vermektir.

KURALLAR:
1. Dil: Her zaman TÜRKÇE cevap ver.
2. Format: Mutlaka aşağıdaki başlıkları kullan:
HÜKÜM: (Özet karar)
GEREKÇE: (Analiz ve dayanak açıklaması)
KAYNAK: (Mevzuat maddesi ve referansı)

3. Reddetme: Eğer bağlamda soruya cevap verecek yeterli veri yoksa tam olarak şunu söyle:
“Bu konuda mevcut veri setinde açık bir hüküm bulunamamıştır.”

4. Güvenlik: Asla kaynak uydurma. Sadece verilen bağlamdaki bilgileri kullan.
"""

    def generate_response(self, question: str) -> Dict[str, Any]:
        """Uçtan uca muhakeme akışı: Retrieve -> Filter -> Structured Inject -> Respond."""
        
        # 1. RAG'dan Hibrit Bağlam Getir
        raw_context = retrieve_context(question)
        
        # 2. Confidence Filtering (Threshold = 0.7)
        filtered_context = [doc for doc in raw_context if doc.get("score", 0) >= self.threshold]
        
        # Ortalama güven skoru hesapla
        avg_confidence = 0.0
        if filtered_context:
            avg_confidence = round(sum(d["score"] for d in filtered_context) / len(filtered_context), 4)

        # 3. Bağlam Kontrolü ve Reddetme Mantığı
        if not filtered_context:
            return {
                "answer": "Bu konuda mevcut veri setinde açık bir hüküm bulunamamıştır.",
                "sources": [],
                "confidence": avg_confidence,
                "status": "refused_by_threshold"
            }

        # 4. Yapılandırılmış Bağlam (Structured Context Injection)
        context_parts = []
        for i, doc in enumerate(filtered_context):
            citation = doc["metadata"].get("exact_citation", "Bilinmeyen Kaynak")
            category = doc["metadata"].get("category", "Genel")
            part = f"[{i+1}] Kural:\n{doc['content']}\n\nKaynak:\n{citation}\n\nKategori:\n{category}\n---"
            context_parts.append(part)
        
        structured_context = "\n\n".join(context_parts)

        # 5. Prompt İnşası
        full_prompt = f"{self.system_prompt}\n\nBAĞLAM:\n{structured_context}\n\nSORU: {question}\n\nCEVAP:"
        
        # 6. Mock Response (Pipeline testi için - Fine-tuned model çıktısını simüle eder)
        return {
            "answer": "HÜKÜM:\nSöz konusu işlem uygun görülmüştür.\n\nGEREKÇE:\nBağlamdaki kurallar çerçevesinde şartlar sağlanmaktadır.\n\nKAYNAK:\n[1] Numaralı Kural",
            "sources": filtered_context,
            "confidence": avg_confidence,
            "raw_prompt": full_prompt
        }

# Singleton instance
inference_engine = FiCOInference()
