import re
from typing import List

class QueryClassifier:
    """FiCO v3.0 Sorgu Sınıflandırma Motoru.
    Sorguları; tanım, karşılaştırma, karar (compliance) ve senaryo olarak kategorize eder.
    """
    
    def __init__(self):
        self.patterns = {
            "definition": [r"nedir", r"tanımı", r"ne demek", r"anlamı"],
            "comparison": [r"farkı", r"karşılaştır", r"kıyasla", r"arasındaki fark"],
            "edge_case": [r"eğer", r"durumunda", r"olursa", r"şartıyla", r"koşuluyla"],
            "compliance_decision": [r"caiz mi", r"uygun mu", r"yasak mı", r"yapılabilir mi", r"hükmü nedir"]
        }

    def classify(self, query: str) -> str:
        """Sorguyu belirlenmiş sınıflardan birine yerleştirir."""
        query = query.lower()
        
        # 1. Compliance Decision (En öncelikli)
        for pattern in self.patterns["compliance_decision"]:
            if re.search(pattern, query):
                return "compliance_decision"
                
        # 2. Comparison
        for pattern in self.patterns["comparison"]:
            if re.search(pattern, query):
                return "comparison"
                
        # 3. Edge Case
        for pattern in self.patterns["edge_case"]:
            if re.search(pattern, query):
                return "edge_case"
                
        # 4. Definition (Varsayılan veya Tanım)
        for pattern in self.patterns["definition"]:
            if re.search(pattern, query):
                return "definition"
                
        return "general_inquiry"

# Singleton instance
query_classifier = QueryClassifier()
