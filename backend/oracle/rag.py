import os
import json
import numpy as np
import chromadb
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer, CrossEncoder
from rank_bm25 import BM25Okapi
from backend.oracle.governance import governance_engine

class RiCOVectorStore:
    """FiCO v3.1 Gelişmiş RAG Motoru (Hybrid + Rerank + Governance)."""
    
    def __init__(self, persist_directory: str = "./backend/data/chroma_db", kb_path: str = "./backend/data/knowledge_base.json"):
        # 1. Embedding Modeli (BAAI/bge-m3)
        self.model = SentenceTransformer("BAAI/bge-m3")
        
        # 2. Reranker (Cross-Encoder)
        self.reranker = CrossEncoder("BAAI/bge-reranker-large")
        
        # 3. ChromaDB (Dense)
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection(
            name="fico_knowledge_v2",
            metadata={"hnsw:space": "cosine"}
        )

        # 4. BM25 (Sparse)
        self.kb_docs = self._load_kb(kb_path)
        self.bm25 = self._init_bm25()

    def _load_kb(self, path: str) -> List[Dict[str, Any]]:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def _init_bm25(self) -> BM25Okapi:
        tokenized_corpus = [self._tokenize(doc["content"]) for doc in self.kb_docs]
        return BM25Okapi(tokenized_corpus)

    def _tokenize(self, text: str) -> List[str]:
        return text.lower().replace(".", "").replace(",", "").split()

    def _deduplicate(self, docs: List[Dict[str, Any]], threshold: float = 0.95) -> List[Dict[str, Any]]:
        if not docs: return []
        unique_docs = [docs[0]]
        for i in range(1, len(docs)):
            is_duplicate = False
            for u_doc in unique_docs:
                if docs[i]["content"] == u_doc["content"]:
                    is_duplicate = True
                    break
            if not is_duplicate:
                unique_docs.append(docs[i])
        return unique_docs

    def search(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """Hibrit arama yapar, yönetişim kurallarını uygular ve rerank yapar."""
        
        # A. HYBRID RETRIEVAL (Top 10 aday)
        candidates = self._hybrid_retrieval(query, k=10)
        
        if not candidates: return []

        # B. GOVERNANCE ANNOTATION (Priority & Recency)
        for cand in candidates:
            source = cand.get("metadata", {}).get("source", cand.get("id", ""))
            updated = cand.get("metadata", {}).get("last_updated", "2020-01-01")
            
            cand["priority_score"] = governance_engine.get_priority_score(source)
            cand["recency_score"] = governance_engine.get_recency_score(updated)

        # C. RERANKING (Semantic Relevance)
        sentence_pairs = [[query, doc["content"]] for doc in candidates]
        rerank_scores = self.reranker.predict(sentence_pairs)
        
        for i, score in enumerate(rerank_scores):
            # Rerank skorunu 0-1 arasına yaklaştırmak için sigmoid benzeri basit bir düzleme (opsiyonel)
            # Burada logit değerleri döner, direkt kullanıyoruz.
            candidates[i]["rerank_score"] = float(score)
            candidates[i]["score"] = float(score)

        # D. POLICY CONFLICT RESOLUTION (v3.1)
        # En yüksek öncelikli dökümanları seç
        candidates = governance_engine.resolve_policy_conflict(candidates)

        # Rerank skoruna göre tekrar sırala
        candidates.sort(key=lambda x: x["rerank_score"], reverse=True)

        # E. DEDUPLICATION & TOP-K
        unique_candidates = self._deduplicate(candidates)
        return unique_candidates[:k]

    def _hybrid_retrieval(self, query: str, k: int = 10) -> List[Dict[str, Any]]:
        query_embedding = self.model.encode([query], normalize_embeddings=True).tolist()
        v_results = self.collection.query(query_embeddings=query_embedding, n_results=k, include=["documents", "metadatas", "distances"])

        dense_scores = {}
        if v_results["ids"]:
            for i, doc_id in enumerate(v_results["ids"][0]):
                dense_scores[doc_id] = 1 - v_results["distances"][0][i]

        tokenized_query = self._tokenize(query)
        bm25_scores = self.bm25.get_scores(tokenized_query)
        max_bm25 = max(bm25_scores) if len(bm25_scores) > 0 and max(bm25_scores) > 0 else 1
        
        hybrid_candidates = []
        for i, doc in enumerate(self.kb_docs):
            d_score = dense_scores.get(doc["id"], 0)
            s_score = bm25_scores[i] / max_bm25
            final_score = (0.7 * d_score) + (0.3 * s_score)
            
            if final_score > 0:
                hybrid_candidates.append({
                    "id": doc["id"],
                    "content": doc["content"],
                    "metadata": doc["metadata"],
                    "hybrid_score": final_score
                })
        
        hybrid_candidates.sort(key=lambda x: x["hybrid_score"], reverse=True)
        return hybrid_candidates[:k]

# Singleton instance
rag_engine = RiCOVectorStore()

def retrieve_context(query: str) -> List[Dict[str, Any]]:
    """FiCO v3.1 Yönetişim Destekli Arama."""
    return rag_engine.search(query)
