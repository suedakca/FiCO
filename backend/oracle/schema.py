from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class ComplianceUnit(BaseModel):
    """Mevzuatın yapısal tek bir birimi (Madde, Tanım veya Şart)."""
    id: str = Field(..., description="Eşsiz kimlik (örn: AAOIFI_STD3_ART2)")
    content: str = Field(..., description="Ham metin içeriği")
    type: str = Field(..., description="Birimin türü: definition | rule | prohibition | exception | condition")
    source: str = Field(..., description="Kaynak (AAOIFI, TKBB, Internal)")
    reference: str = Field(..., description="Tam atıf bilgisi (Standart No, Madde No, Sayfa)")
    tags: List[str] = Field(default_factory=list, description="Kategori etiketleri (örn: Mudaraba, Risk)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Ek meta veriler")

class SFTTrainingSample(BaseModel):
    """Fine-tuning için SFT (Supervised Fine-Tuning) eğitim örneği."""
    instruction: str = Field(..., description="Modelden beklenen talimat/soru")
    context: str = Field(..., description="Modelin kullanması gereken mevzuat bağlamı")
    response: str = Field(..., description="Beklenen ideal, profesyonel yanıt")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="İstatistiksel ve kaynak verileri")

class EvaluationResult(BaseModel):
    """RAGAS veya özel değerlendirme sonuçları."""
    faithfulness: float
    answer_relevance: float
    context_precision: float
    citation_accuracy: float
    hallucination_detected: bool
