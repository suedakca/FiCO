import re
import uuid
from typing import List
from .schema import ComplianceUnit

class RegulationParser:
    """Mevzuat metinlerini yapısal birimlere ayıran uzman ayrıştırıcı."""
    
    def __init__(self):
        # Madde ve Tanım tespiti için regex desenleri
        self.article_pattern = re.compile(r"(Madde|Article)\s*(\d+)[:.]?\s*(.*)", re.IGNORECASE)
        self.definition_pattern = re.compile(r"^(.*?):\s*(.*)", re.MULTILINE)

    def parse_text(self, text: str, source: str, base_ref: str) -> List[ComplianceUnit]:
        """Ham metni parçalara ayırır ve ComplianceUnit listesi döner."""
        units = []
        
        # Basit bazda paragraflara göre bölme (Anlamsal bölme için geliştirilecek)
        chunks = [c.strip() for c in text.split("\n\n") if len(c.strip()) > 50]
        
        for i, chunk in enumerate(chunks):
            unit_type = self._detect_type(chunk)
            unit_id = f"{source}_{uuid.uuid4().hex[:8]}"
            
            unit = ComplianceUnit(
                id=unit_id,
                content=chunk,
                type=unit_type,
                source=source,
                reference=f"{base_ref} - Sekans {i+1}",
                tags=self._extract_tags(chunk)
            )
            units.append(unit)
            
        return units

    def _detect_type(self, text: str) -> str:
        """Metnin türünü tespit eder."""
        lower_text = text.lower()
        if "yasaktır" in lower_text or "caiz değildir" in lower_text:
            return "prohibition"
        if "şarttır" in lower_text or "gereklidir" in lower_text:
            return "condition"
        if "istisna" in lower_text or "ancak" in lower_text:
            return "exception"
        if ":" in text[:30]:
            return "definition"
        return "rule"

    def _extract_tags(self, text: str) -> List[str]:
        """Metinden anahtar kelimeleri (Mudaraba, Faiz, Vade vb.) çıkarır."""
        keywords = ["Mudaraba", "Murabaha", "Faiz", "Sarf", "Sukuk", "Zarar", "Kâr", "Sözleşme"]
        return [k for k in keywords if k.lower() in text.lower()]

# Singleton instance
regulation_parser = RegulationParser()
