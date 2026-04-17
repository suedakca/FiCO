from typing import List, Dict, Any
from .chroma_service import chroma_service
from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

class AgentTools:
    def __init__(self):
        self.llm = ChatOllama(model="bazobehram/turkish-gemma-9b-t1", temperature=0)

    async def document_retriever(self, query: str) -> str:
        """Belgeleri tarar ve en alakalı metin parçalarını kaynak bilgileriyle döner."""
        results = chroma_service.hybrid_search(query, k=3)
        formatted_results = []
        for res in results:
            meta = res["metadata"]
            formatted_results.append(
                f"ID: {meta.get('id')}\n"
                f"Kaynak: {meta.get('source')}\n"
                f"İçerik: {res['content']}\n"
            )
        return "\n\n".join(formatted_results) if formatted_results else "İlgili bilgi bulunamadı."

    async def compliance_validator(self, answer: str, context: str) -> Dict[str, Any]:
        """Üretilen cevabı denetler."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", "Sen bir uyum denetçisisin. Cevap bağlama sadıksa sadece [Pass] yaz. Değilse [Fail] ve kısa bir neden yaz."),
            ("human", "Bağlam: {context}\nCevap: {answer}")
        ])
        chain = prompt | self.llm | StrOutputParser()
        result = await chain.ainvoke({"context": context, "answer": answer})
        
        status = "Pass" if "[Pass]" in result else "Fail"
        return {"status": status, "reason": result}

    async def policy_aggregator(self, category: str) -> str:
        """Farklı kurumlardan (AAOIFI, TKBB, İç Karar) gelen politikaları hiyerarşik olarak birleştirir."""
        # Kategori bazlı tüm belgeleri getir
        all_docs = chroma_service.vector_store._collection.get(
            where={"category": category}
        )
        
        if not all_docs["documents"]:
            return f"{category} kategorisinde kayıtlı mevzuat bulunamadı."
            
        aggregated = [f"**{category.upper()} MEVZUAT BİRLEŞİMİ**"]
        for i, doc in enumerate(all_docs["documents"]):
            meta = all_docs["metadatas"][i]
            aggregated.append(f"Kaynak: {meta.get('source')}\nKural: {doc}\n")
            
        return "\n".join(aggregated)

agent_tools = AgentTools()
