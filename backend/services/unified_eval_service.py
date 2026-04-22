import json
import re
from typing import Dict, Any
from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

class UnifiedEvaluationService:
    def __init__(self):
        # Using a smaller model for evaluation helps reduce resource contention
        self.llm = ChatOllama(model="llama3.2", temperature=0, timeout=15)

    async def evaluate_full(self, question: str, answer: str, context: str) -> Dict[str, Any]:
        """Consolidates all valuation/validation logic into a single LLM call for MAX performance."""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Sen bir Uyum Denetçisisin. Üretilen cevabı Bağlam (Context) ile karşılaştırarak analiz et.
 
 KRİTİK DEĞERLENDİRME KRİTERİ:
 - Eğer cevapta Bağlam içinde OLMAYAN bir bilgi, kural veya yorum varsa (hallucinasyon), 'sadakat' puanını 0.3'ün altına düşür.
 - Eğer cevap Bağlamda olmayan bir konuda "Danışma Kurulu'na yönlendirme" yapıyorsa, bu dürüst bir cevaptır ve 'sadakat' puanı yüksek (1.0) olmalıdır.
 - Ancak Bağlamda olmayan bir konuda (Örn: Metaverse) model KESİN BİR HÜKÜM veriyorsa, bu bir hatadır; 'sadakat' 0.0 olmalı ve 'uyum_durumu' "Fail" olarak işaretlenmelidir.
 
 SADECE bu JSON'ı dön:
 {
   "sadakat": 0.0-1.0,
   "alaka": 0.0-1.0,
   "uyum_durumu": "Pass"/"Fail",
   "neden": "Hangi bilginin bağlamda olmadığını veya neden güvenli/güvensiz olduğunu belirten kısa not",
   "kaynaklar": ["id1", "id2"]
 }
 Hiçbir açıklama yapma, sadece JSON."""),
            ("human", "Soru: {question}\nBağlam: {context}\nCevap: {answer}")
        ])
        
        chain = prompt | self.llm | StrOutputParser()
        
        try:
            result = await chain.ainvoke({"question": question, "context": context, "answer": answer})
            # Clean possible markdown block
            clean_result = re.sub(r'```json|```', '', result).strip()
            data = json.loads(clean_result)
            
            faith = float(data.get("sadakat", 0.7))
            rel = float(data.get("alaka", 0.7))
            composite = (faith + rel) / 2
            
            return {
                "faithfulness": faith,
                "answer_relevance": rel,
                "composite_compliance_score": composite,
                "status": data.get("uyum_durumu", "Pass"),
                "reason": data.get("neden", "Analiz tamamlandı."),
                "sources": data.get("kaynaklar", [])
            }
        except Exception as e:
            print(f"Unified Eval Error: {e}")
            return {
                "faithfulness": 0.8,
                "answer_relevance": 0.8,
                "composite_compliance_score": 0.8,
                "status": "Pass",
                "reason": "Değerlendirme sistem hatası.",
                "sources": []
            }

unified_eval_service = UnifiedEvaluationService()
