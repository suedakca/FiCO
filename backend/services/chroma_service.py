import os
import json
from typing import List, Dict, Any
import numpy as np
from langchain_ollama import OllamaEmbeddings
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
        """Perform Optimized Hybrid Search (Vector + BM25)."""
        # 1. Vector Search (Top k*5 candidates)
        vector_results = self.vector_store.similarity_search_with_relevance_scores(query, k=k*5)
        
        # 2. BM25 Search (Top k*5 candidates)
        tokenized_query = query.lower().split()
        bm25_top_n = self.bm25.get_top_n(tokenized_query, self.bm25_docs, n=k*5)
        
        # 3. Combine Candidates (Removing duplicates)
        candidate_docs = {} # content -> {metadata, vector_score, bm25_score}
        
        # Add vector results
        for doc, score in vector_results:
            candidate_docs[doc.page_content] = {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "vector_score": score,
                "bm25_score": 0.0
            }
            
        # Add BM25 results (Get scores for them)
        bm25_scores = self.bm25.get_scores(tokenized_query)
        # We need original indices to get BM25 scores
        for doc_text in bm25_top_n:
            if doc_text not in candidate_docs:
                idx = self.bm25_docs.index(doc_text)
                candidate_docs[doc_text] = {
                    "content": doc_text,
                    "metadata": self.bm25_metadatas[idx],
                    "vector_score": 0.0,
                    "bm25_score": bm25_scores[idx]
                }
            else:
                idx = self.bm25_docs.index(doc_text)
                candidate_docs[doc_text]["bm25_score"] = bm25_scores[idx]

        # Normalize BM25 scores within candidates if necessary
        max_bm25 = max([c["bm25_score"] for c in candidate_docs.values()]) if candidate_docs else 0
        
        combined_results = []
        for cand in candidate_docs.values():
            b_score = cand["bm25_score"] / max_bm25 if max_bm25 > 0 else 0
            hybrid_score = (cand["vector_score"] * 0.7) + (b_score * 0.3)
            combined_results.append({
                "content": cand["content"],
                "metadata": cand["metadata"],
                "score": hybrid_score
            })
            
        # 4. Reranking Step (Cross-Encoder)
        combined_results.sort(key=lambda x: x["score"], reverse=True)
        candidates = combined_results[:k*3]
        if not candidates:
            return []
            
        pairs = [[query, res["content"]] for res in candidates]
        rerank_scores = self.reranker.predict(pairs)
        
        for i, score in enumerate(rerank_scores):
            candidates[i]["rerank_score"] = float(score)
            
        candidates.sort(key=lambda x: x["rerank_score"], reverse=True)
        filtered_results = [res for res in candidates if res.get("rerank_score", -10) > -2.0]
        
        return filtered_results[:k]

chroma_service = ChromaService()
