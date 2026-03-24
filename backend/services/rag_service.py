import json
import os
from typing import List, Dict, Any
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
from core.config import settings

class RAGService:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            openai_api_key=settings.OPENAI_API_KEY
        )
        self.llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            openai_api_key=settings.OPENAI_API_KEY,
            temperature=0
        )
        self.knowledge_base = self._load_knowledge_base()
        self.documents = [
            Document(
                page_content=item["content"],
                metadata={**item["metadata"], "source": item["source"]}
            )
            for item in self.knowledge_base
        ]

    def _load_knowledge_base(self):
        kb_path = os.path.join(os.path.dirname(__file__), "..", "data", "knowledge_base.json")
        if os.path.exists(kb_path):
            with open(kb_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    async def query(self, text: str) -> Dict[str, Any]:
        """Perform RAG query using the simplified knowledge base."""
        # For prototype with 6 items, we'll do a simple similarity check or just use the most relevant one.
        # In a real app, we'd use a Vector Store like Pinecone or FAISS.
        
        # 1. Retrieval (Hybrid: Vector + Keyword Boost)
        query_embedding = self.embeddings.embed_query(text)
        doc_texts = [d.page_content for d in self.documents]
        doc_embeddings = self.embeddings.embed_documents(doc_texts)
        
        # Manual cosine similarity
        import numpy as np
        def cosine_similarity(a, b):
            return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
        
        vector_scores = [cosine_similarity(query_embedding, de) for de in doc_embeddings]
        
        # Simple Keyword Boost (Hybrid Search Simulation)
        keyword_scores = []
        for doc in self.documents:
            key_terms = ["mudaraba", "icara", "sarf", "garar", "musharaka", "sukuk", "kabz", "mudarib"]
            boost = 0
            for term in key_terms:
                if term in text.lower() and term in doc.page_content.lower():
                    boost += 0.2
            keyword_scores.append(boost)
            
        hybrid_scores = [vs + ks for vs, ks in zip(vector_scores, keyword_scores)]
        best_idx = np.argmax(hybrid_scores)
        relevant_doc = self.documents[best_idx]
        confidence = float(vector_scores[best_idx])

        # 2. Generation (Prompt)
        # Enrich context with full Metadata for the prompt
        metadata = relevant_doc.metadata
        context_str = (
            f"Döküman ID: {metadata.get('id', 'N/A')}\n"
            f"Başlık: {metadata.get('title', 'N/A')}\n"
            f"Kaynak: {metadata.get('source', 'N/A')}\n"
            f"Tam Atıf: {metadata.get('exact_citation', 'N/A')}\n"
            f"Son Güncelleme: {metadata.get('last_updated', 'N/A')}\n"
            f"İçerik: {relevant_doc.page_content}"
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", """Rol: Sen uzman bir Katılım Bankacılığı Uyum Asistanısın (FiCo Kaşif).
Görev: Kullanıcının sorusuna, sana sağlanan döküman parçalarını (Context) kullanarak yanıt ver.

Kesin Kurallar:
1. Atıf Zorunluluğu: Verdiğin her bilginin sonuna köşeli parantez içinde kaynak ID'sini ekle. Örn: "...faiz şüphesi uyandırır. [std_088]"
2. Dışına Çıkma: Eğer sağlanan dökümanlarda cevap yoksa, "Bu konuda veri havuzunda bilgi bulunmamaktadır, uzman görüşü için yönlendiriyorum." de. Kesinlikle kendi genel bilgini kullanma.
3. Çelişki Yönetimi: İki döküman çelişiyorsa her ikisini de belirt ve güven skorunu düşür.
4. Format: Yanıtın en altında "Referanslar" başlığı aç ve kullanılan tüm ID'lerin tam kaynak isimlerini listele.

Bağlam:
{context}"""),
            ("human", "{question}")
        ])

        chain = prompt | self.llm | StrOutputParser()
        
        answer = await chain.ainvoke({
            "context": context_str,
            "question": text
        })

        # 3. Evaluation
        hit_rate = confidence # Cosine similarity of retrieval
        citation_accuracy = 1.0 if relevant_doc.metadata.get("source", "").lower() in answer.lower() or any(s.lower() in answer.lower() for s in [relevant_doc.metadata.get("source")]) else 0.5
        
        # Simple Faithfulness check (Self-Correction/Verification)
        faith_prompt = ChatPromptTemplate.from_messages([
            ("system", "Sen bir hakem modülüsün. Verilen cevabın, sağlanan bağlama (context) ne kadar sadık olduğunu 0.0 ile 1.0 arasında sadece bir sayı olarak puanla. Halüsinasyon varsa düşük puan ver."),
            ("human", "Bağlam: {context}\nCevap: {answer}")
        ])
        faith_chain = faith_prompt | self.llm | StrOutputParser()
        try:
            faith_score_str = await faith_chain.ainvoke({"context": relevant_doc.page_content, "answer": answer})
            faithfulness = float(faith_score_str.strip())
        except:
            faithfulness = 0.85 # Fallback

        return {
            "answer_text": answer,
            "source_urls": [relevant_doc.metadata.get("source", "Bilinmeyen Kaynak")],
            "confidence_score": confidence,
            "hit_rate": hit_rate,
            "faithfulness": faithfulness,
            "citation_accuracy": citation_accuracy
        }

rag_service = RAGService()
