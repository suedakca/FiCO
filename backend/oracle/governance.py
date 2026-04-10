import datetime
from typing import List, Dict, Any

class GovernanceEngine:
    """FiCO v3.2 Kurumsal Yönetişim ve Karar Motoru (Sürüm Kontrollü)."""
    
    def __init__(self):
        # 1. Politika Hiyerarşisi
        self.priority_map = {
            "Kuveyt Türk Uyum Rehberi": 4,
            "Kuveyt Türk İç Fetva Kurulu": 3,
            "TKBB": 2,
            "AAOIFI": 1
        }

    def get_priority_score(self, source: str) -> float:
        score = 1
        for key, value in self.priority_map.items():
            if key.lower() in source.lower():
                score = value
                break
        return score / 4.0

    def select_active_policies(self, chunks: List[Dict[str, Any]], current_date: str = None) -> List[Dict[str, Any]]:
        """Sadece yürürlükte olan politikaları seçer (Effective Date kontrolü)."""
        if not current_date:
            current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        
        active_chunks = []
        for chunk in chunks:
            # Metadata'dan yürürlük tarihini al, yoksa çok eski bir tarih varsay
            effective_date = chunk.get("metadata", {}).get("effective_date", "2000-01-01")
            if effective_date <= current_date:
                active_chunks.append(chunk)
        return active_chunks

    def resolve_policy_conflict(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Aynı konuda çelişen kurallar varsa öncelik ve SÜRÜM kontrolü yapar."""
        if not chunks: return []
        
        # 1. Önceliğe göre sırala
        sorted_chunks = sorted(chunks, key=lambda x: x.get("priority_score", 0), reverse=True)
        max_priority = sorted_chunks[0].get("priority_score", 0)
        
        # 2. En yüksek öncelikli olanları filtrele
        high_priority_chunks = [c for c in sorted_chunks if c.get("priority_score", 0) >= max_priority]
        
        # 3. Aynı öncelik seviyesindekiler arasında en güncel SÜRÜMÜ seç (v2.1 > v2.0)
        # Sürüm formatı "v1.0", "v2.1" gibi varsayılıyor.
        high_priority_chunks.sort(key=lambda x: x.get("metadata", {}).get("version", "v1.0"), reverse=True)
        latest_version = high_priority_chunks[0].get("metadata", {}).get("version", "v1.0")
        
        final_chunks = [c for c in high_priority_chunks if c.get("metadata", {}).get("version", "v1.0") == latest_version]
        return final_chunks

    def get_recency_score(self, last_updated: str) -> float:
        try:
            update_date = datetime.datetime.strptime(last_updated, "%Y-%m-%d")
            today = datetime.datetime.now()
            diff_days = (today - update_date).days
            score = max(0.1, 1.0 - (diff_days / (365 * 3)))
            return round(min(1.0, score), 4)
        except:
            return 0.5

    def should_escalate(self, query: str, chunks: List[Dict[str, Any]], confidence: float, query_type: str) -> bool:
        if confidence < 0.65: return True
        if not chunks: return True
        priorities = [c.get("priority_score", 0) for c in chunks]
        if len(set(priorities)) > 1 and query_type == "compliance_decision":
            return True
        return False

# Singleton instance
governance_engine = GovernanceEngine()
