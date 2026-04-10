import json
import re
from typing import List, Dict, Any
from .chroma_service import chroma_service
from .rag_service import ComplianceAgent # Mevcut ajandan kalıtım alabiliriz veya sarmalayabiliriz

class AdvancedComplianceRAG:
    """Üretim seviyesinde, üst düzey muhakeme ve atıf odaklı RAG motoru."""
    
    def __init__(self):
        self.system_policy = """Sen FiCO (Islamic Finance Compliance Assistant) ajanısın.
GÖREVİN: Sadece verilen 'Bağlam' içindeki bilgileri kullanarak, kesin ve mevzuat diline uygun cevaplar üretmektir.

KURALLAR:
1. Kaynak Gösterme: Her bilginin yanına kaynağını [Kaynak_ID] şeklinde ekle.
2. Kesinlik: Eğer bağlamda yeterli bilgi yoksa "Bağlamda bu soruya cevap verecek yeterli veri bulunmamaktadır" de ve halüsinasyon yapma.
3. Yapı: Cevabını HÜKÜM, GEREKÇE ve KAYNAK bölümlerine ayır.
4. Dil: Sadece profesyonel Türkçe kullan.
"""

    async def analyze_query(self, query: str) -> Dict[str, Any]:
        """Sorguyu analiz eder, hibrit arama yapar ve yapılandırılmış cevap döner."""
        
        # 1. Hibrit Arama (Vektör + BM25)
        # k=4 aday döküman getiriyoruz
        context_docs = chroma_service.hybrid_search(query, k=4)
        
        if not context_docs:
            return {
                "answer": "Üzgünüm, bu konu hakkında mevzuat veritabanımda ilgili bir kayıt bulunamadı.",
                "sources": [],
                "confidence": 0.0
            }

        # 2. Bağlam Hazırlama
        context_text = self._prepare_context(context_docs)
        
        # 3. LLM'e Prompt Hazırlama (Custom Prompt for Fine-tuned Model)
        # Not: Burada rag_service'deki LLM çağrısını özelleştiriyoruz
        prompt = f"{self.system_policy}\n\nBAĞLAM:\n{context_text}\n\nSORU: {query}\n\nCEVAP:"
        
        # Burada modelden yanıt alınacak (v1'deki gibi stream veya sync)
        # Örnek dönüş yapısı:
        return {
            "context": context_text,
            "docs": context_docs,
            "policy": self.system_policy
        }

    def _prepare_context(self, docs: List[Dict[str, Any]]) -> str:
        context_parts = []
        for doc in docs:
            ref = doc["metadata"].get("reference", "Bilinmeyen Kaynak")
            id = doc["metadata"].get("id", "N/A")
            context_parts.append(f"[{id}] (Referans: {ref}): {doc['content']}")
        return "\n\n".join(context_parts)

# Singleton instance
advanced_rag = AdvancedComplianceRAG()
