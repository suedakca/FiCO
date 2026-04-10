import hashlib
from typing import Dict, Any, Optional

class QueryCache:
    """FiCO v3.2 Deterministik Yanıt Önbelleği.
    Aynı normalize edilmiş sorgunun her zaman aynı sonucu üretmesini sağlar.
    """
    
    def __init__(self, limit: int = 1000):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.limit = limit

    def generate_key(self, normalized_query: str) -> str:
        """Sorgu için benzersiz bir SHA-256 hash anahtarı üretir."""
        return hashlib.sha256(normalized_query.encode("utf-8")).hexdigest()

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Önbellekten sonuç döner."""
        return self._cache.get(key)

    def set(self, key: str, response: Dict[str, Any]):
        """Sonucu önbelleğe kaydeder."""
        if len(self._cache) >= self.limit:
            # Basit temizleme: En eski kaydı sil (LIFO/FIFO basitlik için)
            first_key = next(iter(self._cache))
            del self._cache[first_key]
        self._cache[key] = response

# Singleton instance
query_cache = QueryCache()
