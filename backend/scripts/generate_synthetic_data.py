import json
import os
import asyncio
from typing import List, Dict
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from tqdm import tqdm

# Yapılandırma
MODEL_NAME = "llama3.2"
INPUT_FILE = "backend/data/knowledge_base.json"
OUTPUT_FILE = "backend/data/synthetic_data.json"
ITERATIONS_PER_CATEGORY = 6 # Her kategori (QA, Case, Adv) için kaç kez sorulacak

class SyntheticDataGenerator:
    def __init__(self):
        self.llm = ChatOllama(model=MODEL_NAME, temperature=0.85)
        self.parser = JsonOutputParser()
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """Sen Katılım Bankacılığı Uyum Uzmanısın. 
Görevin, verilen mevzuat bilgilerinden eğitim verisi üretmektir.

### KESİN KURALLAR (HATA KABUL EDİLMEZ):
1. **DİL KİLİDİ (TURKISH ONLY):** Tüm çıktı %100 doğal ve akıcı Türkçe olmalıdır. 
   - ASLA İngilizce kelime kullanma (Örn: "information", "context", "provided", "failure" yasaktır).
   - ASLA Almanca veya diğer dillerden kelime sızdırma (Örn: "verwendet", "använd" yasaktır).
   - Teknik terimlerin en doğru Türkçe karşılıklarını kullan.
2. **ÇEŞİTLİLİK:** Her örnek özgün cümle yapılarına sahip olmalıdır.
3. **KATEGORİ UYUMU:** 
   - 'direct_qa': Net ve doğrudan bilgi.
   - 'case_study': "Bir müşteri..." ile başlayan gerçekçi bankacılık senaryoları.
   - 'adversarial': Kuralları zorlayan kullanıcıya verilen reddedici uyum cevabı.

ÇIKTI FORMATI (SADECE JSON - BÜYÜK HARF VE TÜRKÇE KARAKTER KULLANILABİLİR):
[
  {{"instruction": "soru cümlesi", "context": "sorunun bağlamı veya senaryo açıklaması", "response": "detaylı ve doğru cevap"}}
]"""),
            ("human", "Kategori: {category}\nİlgili Mevzuat:\n{content}")
        ])
        
        self.chain = self.prompt | self.llm | self.parser

    async def generate_single_sample(self, entry: Dict, category: str, round_num: int) -> List[Dict]:
        """Tek bir kategori için spesifik bir örnek üretir."""
        
        try:
            results = await self.chain.ainvoke({
                "category": category,
                "content": entry['content']
            })
            
            if isinstance(results, dict): results = [results]
            
            final = []
            if isinstance(results, list):
                for res in results:
                    if isinstance(res, dict) and "instruction" in res:
                        res["category"] = category
                        res["original_id"] = entry["id"]
                        res["source"] = entry["source"]
                        final.append(res)
            
            if final:
                print(f"  [OK] - {entry['id']} - {category} ({len(final)} örnek)")
            return final
        except Exception as e:
            # print(f"  [HATA] - {entry['id']} - {category}: {e}")
            return []

async def main():
    generator = SyntheticDataGenerator()
    
    if not os.path.exists(INPUT_FILE):
        print(f"Hata: {INPUT_FILE} bulunamadı.")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        kb_data = json.load(f)

    all_synthetic_data = []
    print(f"🚀 {len(kb_data)} ana madde üzerinden SERİ ÜRETİM (Dil Kilitli) başlıyor...")
    print(f"Hedef: ~{len(kb_data) * 3 * ITERATIONS_PER_CATEGORY * 2} örnek.")

    categories = ["direct_qa", "case_study", "adversarial"]

    for entry in tqdm(kb_data):
        for cat in categories:
            for i in range(ITERATIONS_PER_CATEGORY):
                samples = await generator.generate_single_sample(entry, cat, i)
                all_synthetic_data.extend(samples)
                await asyncio.sleep(0.1)
        
        # Ara kaydet
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(all_synthetic_data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ İşlem tamamlandı! Toplam {len(all_synthetic_data)} adet sentetik veri üretildi.")

if __name__ == "__main__":
    asyncio.run(main())
