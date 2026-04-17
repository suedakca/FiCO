import os

def create_fused_modelfile():
    """Eğitilmiş LoRA adapter'larını kullanarak yeni bir Ollama Modelfile oluşturur."""
    
    adapter_path = "training/adapters/adapter.safetensors"
    base_model = "llama3.2:3b" # Veya gemma:9b
    new_model_name = "fico-expert-model"

    if not os.path.exists(adapter_path):
        print(f"Hata: Adapter dosyası bulunamadı ({adapter_path}). Lütfen önce eğitimi tamamlayın.")
        return

    modelfile_content = f"""
FROM {base_model}
ADAPTER {os.path.abspath(adapter_path)}

# FiCO Spesifik Sistem Promptu
SYSTEM "Sen Katılım Bankacılığı konusunda uzmanlaşmış bir Uyum Analistisin. Sadece Türkçe konuşur ve fıkhi standartlara (AAOIFI/TKBB) %100 sadık kalırsın."

PARAMETER temperature 0.3
PARAMETER top_p 0.9
"""

    with open("Modelfile_fused", "w", encoding="utf-8") as f:
        f.write(modelfile_content)

    print(f"Yeni Modelfile ('Modelfile_fused') başarıyla oluşturuldu.")
    print(f"Şu komutu çalıştırarak modeli Ollama'ya ekleyebilirsiniz:")
    print(f"ollama create {new_model_name} -f Modelfile_fused")

if __name__ == "__main__":
    create_fused_modelfile()
