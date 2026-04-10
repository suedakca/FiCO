import os
import json
import numpy as np
import chromadb
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi

class RiCOVectorStore:
    """FiCO için hibrit arama (Dense + Sparse) destekli üretim seviyesi RAG motoru."""
    
    def __init__(self, persist_directory: str = "./backend/data/chroma_db", kb_path: str = "./backend/data/knowledge_base.json"):
        # 1. Embedding Modeli (BAAI/bge-m3) - Üretim Sınıfı
        self.model = SentenceTransformer("BAAI/bge-m3")
        
        # 2. ChromaDB (Dense)
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection(
            name="fico_knowledge_v2",
            metadata={"hnsw:space": "cosine"}
        )

        # 3. BM25 (Sparse) Hazırlığı
        self.kb_docs = self._load_kb(kb_path)
        self.bm25 = self._init_bm25()

    def _load_kb(self, path: str) -> List[Dict[str, Any]]:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def _init_bm25(self) -> BM25Okapi:
        """BM25 için dökümanları tokenize eder ve indeksler."""
        tokenized_corpus = [self._tokenize(doc["content"]) for doc in self.kb_docs]
        return BM25Okapi(tokenized_corpus)

    def _tokenize(self, text: str) -> List[str]:
        """Basit ama etkili temizleme ve tokenizasyon."""
        return text.lower().replace(".", "").replace(",", "").split()

    def hybrid_search(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """Dense ve Sparse aramayı birleştirerek en alakalı 3 dökümanı döner."""
        
        # A. DENSE SEARCH (Vektör)
        query_embedding = self.model.encode([query], normalize_embeddings=True).tolist()
        v_results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=10, # Birleştirme için geniş liste alıyoruz
            include=["documents", "metadatas", "distances"]
        )

        # Vektör sonuçlarını bir sözlükte topla (ID -> Score)
        # Chroma cosine distance (0-2), 1-dist/2 = similarity (tek yönlü)
        dense_scores = {}
        if v_results["ids"]:
            for i, doc_id in enumerate(v_results["ids"][0]):
                sim = 1 - (v_results["distances"][0][i]) 
                dense_scores[doc_id] = sim

        # B. SPARSE SEARCH (BM25)
        tokenized_query = self._tokenize(query)
        bm25_scores = self.bm25.get_scores(tokenized_query)
        
        # BM25 Skorlarını normalleştir (0-1)
        max_bm25 = max(bm25_scores) if len(bm25_scores) > 0 and max(bm25_scores) > 0 else 1
        bm25_norm_scores = {self.kb_docs[i]["id"]: (bm25_scores[i] / max_bm25) for i in range(len(bm25_scores))}

        # C. MERGE & SCORE (Weighted Scoring)
        hybrid_results = []
        all_ids = set(list(dense_scores.keys()) + list(bm25_norm_scores.keys()))

        for doc_id in all_ids:
            d_score = dense_scores.get(doc_id, 0)
            s_score = bm25_norm_scores.get(doc_id, 0)
            
            # Hibrit Skor: 0.7 Dense + 0.3 Sparse
            final_score = (0.7 * d_score) + (0.3 * s_score)
            
            # Orijinal döküman verisini bul
            doc_data = next((d for d in self.kb_docs if d["id"] == doc_id), None)
            if doc_data:
                hybrid_results.append({
                    "id": doc_id,
                    "content": doc_data["content"],
                    "metadata": doc_data["metadata"],
                    "score": round(final_score, 4)
                })

        # Skorlara göre sırala ve top-k döndür
        hybrid_results.sort(key=lambda x: x["score"], reverse=True)
        return hybrid_results[:k]

    def add_documents(self, documents: List[Dict[str, Any]]):
        """Yeni döküman ekleme (Vektör tabanı için)."""
        ids = [doc["id"] for doc in documents]
        texts = [doc["content"] for doc in documents]
        metadatas = [doc["metadata"] for doc in documents]
        
        embeddings = self.model.encode(texts, normalize_embeddings=True).tolist()
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )
        print(f"✅ {len(ids)} döküman vektör tabanına eklendi.")

# Singleton instance
rag_engine = RiCOVectorStore()

def retrieve_context(query: str) -> List[Dict[str, Any]]:
    """Dışarıdan erişim için sarmalayıcı (Hibrit Arama)."""
    return rag_engine.hybrid_search(query)
