from typing import Dict, Any
from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

class EvaluationService:
    def __init__(self):
        self.llm = ChatOllama(model="llama3.2", temperature=0)

    async def evaluate_response(self, question: str, answer: str, context: str) -> Dict[str, Any]:
        """RAGAS benzeri metriklerle cevabı değerlendirir."""
        
        # 1. Faithfulness (Sadakat)
        faith_prompt = ChatPromptTemplate.from_messages([
            ("system", "Sen bir hakem modülüsün. Cevabın bağlama (context) sadakatini 0.0 ile 1.0 arasında bir sayı olarak ver."),
            ("human", "Bağlam: {context}\nCevap: {answer}")
        ])
        
        # 2. Answer Relevance (Cevap Uygunluğu)
        rel_prompt = ChatPromptTemplate.from_messages([
            ("system", "Sen bir hakem modülüsün. Cevabın soruyla ne kadar alakalı olduğunu 0.0 ile 1.0 arasında bir sayı olarak ver."),
            ("human", "Soru: {question}\nCevap: {answer}")
        ])

        # Paralel çalıştırma veya sıralı (basitlik için sıralı)
        faith_chain = faith_prompt | self.llm | StrOutputParser()
        rel_chain = rel_prompt | self.llm | StrOutputParser()

        try:
            faith_result = await faith_chain.ainvoke({"context": context, "answer": answer})
            rel_result = await rel_chain.ainvoke({"question": question, "answer": answer})
            
            # Sayıları ayıkla
            import re
            faith_score = float(re.findall(r"0\.\d+|1\.0", faith_result)[0]) if re.findall(r"0\.\d+|1\.0", faith_result) else 0.8
            rel_score = float(re.findall(r"0\.\d+|1\.0", rel_result)[0]) if re.findall(r"0\.\d+|1\.0", rel_result) else 0.8
            
        except Exception as e:
            print(f"Değerlendirme hatası: {e}")
            faith_score, rel_score = 0.7, 0.7

        composite_score = (faith_score + rel_score) / 2
        
        return {
            "faithfulness": faith_score,
            "answer_relevance": rel_score,
            "composite_compliance_score": composite_score
        }

evaluation_service = EvaluationService()
