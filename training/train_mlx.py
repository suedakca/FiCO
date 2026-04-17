import mlx.core as mx
import mlx.nn as nn
from mlx_lm import load, generate, lora
from mlx_lm.tuner import train, TrainingArgs
import json
import os

# YAPILANDIRMA
MODEL_PATH = "mlp-dot-dev/llama-3.2-3b-it-mlx-4bit" # Mac dostu 4-bit model
DATA_PATH = "backend/data/fico_train_dataset.jsonl"
ADAPTER_PATH = "training/adapters"

def start_training():
    """MLX kullanarak LoRA tabanlı ince ayar (fine-tuning) başlatır."""
    
    if not os.path.exists(DATA_PATH):
        print(f"Hata: Veri seti bulunamadı ({DATA_PATH}).")
        return

    print(f"Model yükleniyor: {MODEL_PATH}")
    model, tokenizer = load(MODEL_PATH)
    
    # Eğitim parametreleri
    args = TrainingArgs(
        batch_size=1,
        iters=500, # 16GB RAM için 500-1000 iterasyon idealdir
        learning_rate=1e-5,
        steps_per_report=10,
        steps_per_eval=50,
        adapter_file=ADAPTER_PATH + "/adapter.safetensors",
    )

    print("Eğitim başlatılıyor. Bu işlem Mac hızına ve veri miktarına göre süre alabilir...")
    
    # MLX-LM tuner kullanarak eğitimi başlat
    # Not: Bu fonksiyon genellikle komut satırı aracı (mlx_lm.lora) ile çağrılır 
    # ancak burada temel yapılandırmayı sunuyoruz.
    
    print("\n[BİLGİ] Eğitimi başlatmak için terminalde şu komutu çalıştırmanız önerilir:")
    print(f"python -m mlx_lm.lora --model {MODEL_PATH} --data {os.path.dirname(DATA_PATH)} --train --iters 500")

if __name__ == "__main__":
    start_training()
