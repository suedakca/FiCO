import json
import os
import asyncio
from typing import List, Dict
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from tqdm import tqdm

# Yapılandırma
MODEL_NAME = "llama3.2" # Veri üretimi için hızlı modeller tercih edilir
INPUT_FILE = "backend/data/knowledge_base.json"
OUTPUT_FILE = "backend/data/synthetic_data.json"

class SyntheticDataGenerator:
    def __init__(self):
        self.llm = ChatOllama(model=MODEL_NAME, temperature=0.8, format="json")
        self.parser = JsonOutputParser()

    async def generate_variants(self, entry: Dict) -> List[Dict]:
        """Bir bilgi maddesi için farklı formatlarda sentetik veri üretir."""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Sen Katılım Bankacılığı konusunda uzman bir veri setleri üreticisisin. 
Görevin, verilen bir mevzuat maddesini kullanarak eğitim için yüksek kaliteli soru-cevap çiftleri üretmektir.

Üreteceğin her örnek şu 3 tipi içermelidir:
1. "direct_qa": Standart hakkında doğrudan bilgi soran soru.
2. "case_study": Gerçek hayattan bir senaryo içeren ve çözüm sunan soru.
3. "adversarial": Kullanıcının kuralı ihlal etmeye veya esnetmeye çalıştığı, senin doğruyu savunduğun soru.

Yanıtını şu JSON formatında ver:
[
  {{"instruction": "soru", "context": "bağlam", "response": "cevap", "category": "tip"}},
  ...
]
DİL: Sadece Türkçe kullan.
"""),
            ("human", f"Mevzuat Maddesi:\n{entry['content']}\n\nKaynak: {entry['source']}")
        ])

        chain = prompt | self.llm | self.parser
        
        try:
            results = await chain.ainvoke({})
            # Her birine orijinal ID ve meta verileri ekle
            for res in results:
                res["original_id"] = entry["id"]
                res["source"] = entry["source"]
            return results
        except Exception as e:
            print(f"Hata ({entry['id']}): {e}")
            return []

async def main():
    generator = SyntheticDataGenerator()
    
    if not os.path.exists(INPUT_FILE):
        print(f"Hata: {INPUT_FILE} bulunamadı.")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        kb_data = json.load(f)

    all_synthetic_data = []
    print(f"{len(kb_data)} ana madde üzerinden veri üretimi başlıyor...")

    for entry in tqdm(kb_data):
        variants = await generator.generate_variants(entry)
        all_synthetic_data.extend(variants)
        # Çok hızlı gidip Ollama'yı yormamak için kısa bir ara
        await asyncio.sleep(0.5)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_synthetic_data, f, ensure_ascii=False, indent=2)

    print(f"İşlem tamamlandı. {len(all_synthetic_data)} adet sentetik veri {OUTPUT_FILE} dosyasına kaydedildi.")

if __name__ == "__main__":
    asyncio.run(main())
