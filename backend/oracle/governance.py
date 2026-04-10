import datetime
from typing import List, Dict, Any

class GovernanceEngine:
    """FiCO v3.1 Kurumsal Yönetişim ve Karar Motoru."""
    
    def __init__(self):
        # 1. Politika Hiyerarşisi (4: En Yüksek, 1: En Düşük)
        self.priority_map = {
            "Kuveyt Türk Uyum Rehberi": 4,
            "Kuveyt Türk İç Fetva Kurulu": 3,
            "TKBB": 2,
            "AAOIFI": 1
        }

    def get_priority_score(self, source: str) -> float:
        """Kaynağa göre öncelik skoru döner (0.0 - 1.0 arası normalize)."""
        score = 1 # Varsayılan en düşük
        for key, value in self.priority_map.items():
            if key.lower() in source.lower():
                score = value
                break
        return score / 4.0 # 0.25 - 1.0 arası

    def get_recency_score(self, last_updated: str) -> float:
        """Dökümanın güncelliğine göre skor döner (Son 2 yıl baz alınır)."""
        try:
            update_date = datetime.datetime.strptime(last_updated, "%Y-%m-%d")
            today = datetime.datetime.now()
            diff_days = (today - update_date).days
            # 730 gün (2 yıl) içerisinde ise güncel sayılır, değilse lineer azalır
            score = max(0.1, 1.0 - (diff_days / (365 * 3))) # 3 yıla kadar ölçekle
            return round(min(1.0, score), 4)
        except:
            return 0.5 # Tarih yoksa nötr skor

    def resolve_policy_conflict(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Aynı konuda çelişen kurallar varsa yüksek öncelikli olanı baskın kılar."""
        if not chunks: return []
        
        # Önceliklere göre sırala (Yüksek öncelik en üstte)
        sorted_chunks = sorted(chunks, key=lambda x: x.get("priority_score", 0), reverse=True)
        
        # v3.1 Mantığı: En yüksek öncelik seviyesini bul
        max_priority = sorted_chunks[0].get("priority_score", 0)
        
        # Sadece en yüksek öncelikli olanları veya ona çok yakın olanları tut (Strict Policy)
        # Örn: Banka politikası varken AAOIFI devre dışı kalır.
        final_chunks = [c for c in sorted_chunks if c.get("priority_score", 0) >= max_priority]
        
        return final_chunks

    def should_escalate(self, query: str, chunks: List[Dict[str, Any]], confidence: float, query_type: str) -> bool:
        """Vakanın insan denetimine (Danışma Kurulu) gitmesi gerekip gerekmediğine karar verir."""
        
        # 1. Güven eşiği çok düşükse
        if confidence < 0.65:
            return True
        
        # 2. Hiç döküman bulunamadıysa
        if not chunks:
            return True
            
        # 3. Yüksek öncelikli kurallar arasında çelişki varsa
        priorities = [c.get("priority_score", 0) for c in chunks]
        if len(set(priorities)) > 1 and query_type == "compliance_decision":
            # Farklı hiyerarşilerden kurallar gelmişse ve soru kritikse eskalasyon önerilir
            return True
            
        return False

# Singleton instance
governance_engine = GovernanceEngine()
