import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from services.chroma_service import chroma_service

if __name__ == "__main__":
    print("ChromaDB başlatılıyor ve veriler senkronize ediliyor...")
    # chroma_service initialization handles sync
    print(f"Bitti. Toplam belge sayısı: {chroma_service.vector_store._collection.count()}")
