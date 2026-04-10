import json
import random
from typing import List
from .schema import ComplianceUnit, SFTTrainingSample

class SyntheticDataGenerator:
    """Mevzuat birimlerinden eğitici SFT veri setleri üreten motor."""
    
    def __init__(self, target_samples_per_unit: int = 3):
        self.target_samples_per_unit = target_samples_per_unit

    async def generate_samples(self, units: List[ComplianceUnit]) -> List[SFTTrainingSample]:
        """Birimleri işleyerek çeşitlendirilmiş eğitim örnekleri oluşturur."""
        all_samples = []
        
        for unit in units:
            # Her birim için farklı görev türleri oluştur
            # 1. Doğrudan Bilgi Sorusu (Definition/Rule)
            all_samples.append(self._create_direct_sample(unit))
            
            # 2. Senaryo Bazlı Akıl Yürütme
            all_samples.append(self._create_scenario_sample(unit))
            
            # 3. Negatif Örnek (Reddetme/Refusal)
            if unit.type == "prohibition":
                all_samples.append(self._create_refusal_sample(unit))
                
        return all_samples

    def _create_direct_sample(self, unit: ComplianceUnit) -> SFTTrainingSample:
        """Doğrudan mevzuat bilgisini sorgulayan örnek."""
        instruction = f"{unit.source} standartlarına göre {unit.tags[0] if unit.tags else 'bu konu'} hakkındaki kural nedir?"
        
        return SFTTrainingSample(
            instruction=instruction,
            context=unit.content,
            response=f"HÜKÜM: {unit.content}\n\nKAYNAK: {unit.reference}",
            metadata={"type": "definition", "source": unit.source, "ref": unit.reference}
        )

    def _create_scenario_sample(self, unit: ComplianceUnit) -> SFTTrainingSample:
        """Senaryo üzerinden akıl yürütme örneği."""
        # Not: Gerçek uygulamada bu kısım bir LLM (GPT-4/Claude) tarafından üretilmelidir.
        # Burada şablon bir yapı sunuyoruz.
        scenario = f"Bir müşteri {unit.tags[0] if unit.tags else 'bu hizmet'} ile ilgili bir işlem yapmak istiyor..."
        instruction = f"Aşağıdaki senaryoyu {unit.source} kuralları çerçevesinde analiz et:\n{scenario}"
        
        return SFTTrainingSample(
            instruction=instruction,
            context=unit.content,
            response=f"ANALİZ: Senaryo incelendiğinde {unit.content} maddesi gereği işlem yapılabilir.\n\nGEREKÇE: Mevzuatta belirtilen şartlar sağlanmaktadır.\n\nKAYNAK: {unit.reference}",
            metadata={"type": "scenario", "source": unit.source, "ref": unit.reference}
        )

    def _create_refusal_sample(self, unit: ComplianceUnit) -> SFTTrainingSample:
        """Hatalı/Yasak işlem taleplerini reddetme örneği."""
        instruction = f"Müşteri {unit.tags[0] if unit.tags else 'bu'} konuda yasaklanmış bir işlem talep ederse nasıl yanıt vermelisin?"
        
        return SFTTrainingSample(
            instruction=instruction,
            context=unit.content,
            response=f"HÜKÜM: Bu işlem {unit.source} prensiplerine göre caiz değildir.\n\nNEDEN: {unit.content}\n\nKAYNAK: {unit.reference}",
            metadata={"type": "refusal", "source": unit.source, "ref": unit.reference}
        )

# Singleton instance
data_generator = SyntheticDataGenerator()
