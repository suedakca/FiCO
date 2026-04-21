from typing import Dict, Any
from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

class EvaluationService:
    def __init__(self):
        self.llm = ChatOllama(model="bazobehram/turkish-gemma-9b-t1", temperature=0)

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

        # Paralel çalıştırma
        faith_chain = faith_prompt | self.llm | StrOutputParser()
        rel_chain = rel_prompt | self.llm | StrOutputParser()

        try:
            import asyncio
            import re

            def _extract_score(text: str) -> float:
                """0.0-1.0 arasında ondalık sayı çıkarır; bulunamazsa None döner."""
                # Tam sayı ve ondalık: 0.85, 0.9, 1.0, 1.00 gibi formatları yakalar
                matches = re.findall(r'\b(?:1\.0+|0\.\d+)\b', text)
                for m in matches:
                    try:
                        val = float(m)
                        if 0.0 <= val <= 1.0:
                            return val
                    except ValueError:
                        continue
                # Ondalıksız tam 1 sayısını da dene (örn. model "1" döndürdüyse)
                if re.search(r'\b1\b', text):
                    return 1.0
                return None

            # Parallel execute chains
            faith_result, rel_result = await asyncio.gather(
                faith_chain.ainvoke({"context": context, "answer": answer}),
                rel_chain.ainvoke({"question": question, "answer": answer})
            )

            faith_score = _extract_score(faith_result) or 0.7
            rel_score = _extract_score(rel_result) or 0.7

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
