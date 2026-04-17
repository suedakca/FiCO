import json
import os

SYNTHETIC_FILE = "backend/data/synthetic_data.json"
TRAIN_FILE = "backend/data/fico_train_dataset.jsonl"

def convert_to_alpaca():
    """Sentetik veriyi Alpaca formatına (.jsonl) dönüştürür."""
    if not os.path.exists(SYNTHETIC_FILE):
        print(f"Hata: {SYNTHETIC_FILE} bulunamadı. Lütfen önce generate_synthetic_data.py scriptini çalıştırın.")
        return

    with open(SYNTHETIC_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    with open(TRAIN_FILE, "w", encoding="utf-8") as f:
        for entry in data:
            # ReAct benzeri bir akıl yürütme katmanı eklemek için prompt yapısını düzenliyoruz
            instruction = entry.get("instruction", "")
            context = entry.get("context", "")
            response = entry.get("response", "")
            
            # Alpaca formatı: instruction, input (context), output
            alpaca_entry = {
                "instruction": instruction,
                "input": context,
                "output": response
            }
            f.write(json.dumps(alpaca_entry, ensure_ascii=False) + "\n")

    print(f"Başarılı: {len(data)} örnek {TRAIN_FILE} dosyasına Alpaca formatında kaydedildi.")

if __name__ == "__main__":
    convert_to_alpaca()
