import json
import time
import os
from typing import Dict, Any

class FeedbackLoop:
    """FiCO v3.2 Geri Bildirim ve Öz-İyileştirme Döngüsü.
    Kullanıcı geri bildirimlerini toplar ve ileride model eğitimi için saklar.
    """
    
    def __init__(self, feedback_file: str = "./backend/data/feedback.jsonl"):
        self.feedback_file = feedback_file
        # Dizin yoksa oluştur
        os.makedirs(os.path.dirname(self.feedback_file), exist_ok=True)

    def record_feedback(self, data: Dict[str, Any]):
        """Geri bildirimi JSONL formatında kaydeder."""
        entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            **data
        }
        with open(self.feedback_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

# Singleton instance
feedback_loop = FeedbackLoop()
