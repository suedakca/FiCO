import asyncio
import os
import sys

# Add backend to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.rag_service import rag_service

async def run_tests():
    scenarios = [
        {
            "name": "Çelişki Testi (Mudaraba Zararı)",
            "query": "Müşterinin borcu nedeniyle oluşan zararı işletmeciden alabilir miyiz?",
            "expected_source": "AAOIFI-Sharia-Standard-13"
        },
        {
            "name": "Sınır Testi (Kripto Teminat)",
            "query": "Kripto parayı teminat alabilir miyiz?",
            "expected_source": "KT-Ic-Fetva-2025"
        },
        {
            "name": "Hukuki Nüans (Vadeli Döviz)",
            "query": "Döviz işlemini vadeli yapabilir miyiz?",
            "expected_source": "AAOIFI-Sharia-Standard-5"
        }
    ]

    print("--- FiCo Kaşif RAG Test Senaryoları ---\n")
    
    # Check for API Key
    if not os.getenv("OPENAI_API_KEY"):
        print("UYARI: OPENAI_API_KEY ayarlı değil. Gerçek RAG testi yapılamıyor.")
        print("Lütfen .env dosyanıza API anahtarınızı ekleyin.\n")
        return

    for s in scenarios:
        print(f"Senaryo: {s['name']}")
        print(f"Soru: {s['query']}")
        try:
            result = await rag_service.query(s['query'])
            print(f"Cevap: {result['answer_text']}")
            print(f"Kaynak: {result['source_urls']}")
            print(f"Güven Skoru: {result['confidence_score']:.2f}")
            
            if s['expected_source'] in result['source_urls']:
                print("DURUM: ✅ TEST BAŞARILI (Doğru Kaynak Bulundu)")
            else:
                print(f"DURUM: ❌ TEST BAŞARISIZ (Beklenen Kaynak: {s['expected_source']})")
        except Exception as e:
            print(f"Hata: {str(e)}")
        print("-" * 40)

if __name__ == "__main__":
    asyncio.run(run_tests())
