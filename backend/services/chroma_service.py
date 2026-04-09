import os
import json
from typing import List, Dict, Any
import numpy as np
from langchain_community.embeddings import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder

class ChromaService:
    def __init__(self):
        self.embeddings = OllamaEmbeddings(model="nomic-embed-text")
        self.persist_directory = os.path.join(os.path.dirname(__file__), "..", "data", "chroma_db")
        self.collection_name = "fico_knowledge"
        
        # Initialize Reranker (Cross-Encoder)
        self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        
        # Initialize Chroma
        self.vector_store = Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embeddings,
            persist_directory=self.persist_directory,
            collection_metadata={"hnsw:space": "cosine"}
        )
        
        self.kb_path = os.path.join(os.path.dirname(__file__), "..", "data", "knowledge_base.json")
        self._sync_knowledge_base()
        self._initialize_bm25()

    def _sync_knowledge_base(self):
        """Sync local JSON knowledge base with ChromaDB."""
        if not os.path.exists(self.kb_path):
            return

        with open(self.kb_path, "r", encoding="utf-8") as f:
            kb_data = json.load(f)

        # Simple check: if collection is empty, load all
        # In production, we'd use IDs to check for updates
        existing_count = self.vector_store._collection.count()
        if existing_count == 0:
            documents = []
            for item in kb_data:
                doc = Document(
                    page_content=item["content"],
                    metadata={
                        **item.get("metadata", {}),
                        "source": item.get("source", "N/A"),
                        "id": item.get("id", "N/A")
                    }
                )
                documents.append(doc)
            
            if documents:
                self.vector_store.add_documents(documents)
                print(f"✅ ChromaDB sync tamamlandı: {len(documents)} döküman eklendi.")

    def _initialize_bm25(self):
        """Initialize BM25 for keyword search."""
        # Get all documents from vector store for BM25
        # Since this is a small collection, we can keep it in memory
        results = self.vector_store._collection.get()
        self.bm25_docs = results["documents"]
        self.bm25_metadatas = results["metadatas"]
        
        # Tokenize Turkish text (simple split for now, can be improved)
        tokenized_corpus = [d.lower().split() for d in self.bm25_docs]
        self.bm25 = BM25Okapi(tokenized_corpus)

    def hybrid_search(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """Perform Hybrid Search (Vector + BM25)."""
        # 1. Vector Search
        vector_results = self.vector_store.similarity_search_with_relevance_scores(query, k=k*2)
        
        # 2. BM25 Search
        tokenized_query = query.lower().split()
        bm25_scores = self.bm25.get_scores(tokenized_query)
        
        # Normalize BM25 scores to [0, 1]
        if len(bm25_scores) > 0 and max(bm25_scores) > 0:
            bm25_scores = bm25_scores / max(bm25_scores)
        
        # 3. Re-ranking (Simple Combination)
        # Combine vector relevance and BM25 scores
        combined_results = []
        
        # Create a map for vector results
        vector_map = {doc.page_content: score for doc, score in vector_results}
        
        for i, doc_text in enumerate(self.bm25_docs):
            v_score = vector_map.get(doc_text, 0.0)
            b_score = bm25_scores[i]
            
            # Hybrid Score (Weighted Average)
            hybrid_score = (v_score * 0.7) + (b_score * 0.3)
            
            combined_results.append({
                "content": doc_text,
                "metadata": self.bm25_metadatas[i],
                "score": hybrid_score
            })
            
        # 3. Reranking Step (Cross-Encoder ile Yeniden Sıralama)
        # Sadece ilk k*3 adayı rerank ederek performansı koru
        candidates = combined_results[:k*3]
        if not candidates:
            return []
            
        pairs = [[query, res["content"]] for res in candidates]
        rerank_scores = self.reranker.predict(pairs)
        
        # Update scores with reranker scores
        for i, score in enumerate(rerank_scores):
            candidates[i]["rerank_score"] = float(score)
            
        # Re-sort based on reranker score
        candidates.sort(key=lambda x: x["rerank_score"], reverse=True)
        
        # Threshold Filter (Budama): Rerank skoru 0'ın üzerindekileri al (Logit skalası)
        # Cross-encoder skoru genellikle 0 etrafındadır, alakasızlar negatiftir
        filtered_results = [res for res in candidates if res.get("rerank_score", -10) > -2.0]
        
        return filtered_results[:k]

chroma_service = ChromaService()
