from dataclasses import dataclass, field
from typing import Optional

@dataclass
class TrainingConfig:
    """FiCO Fine-tuning konfigürasyonu (Unsloth & QLoRA optimize)."""
    
    # Model Ayarları
    model_name: str = "unsloth/gemma-4b-it-bnb-4bit" # 16GB VRAM için 4B veya 9B seçilebilir
    max_seq_length: int = 2048
    load_in_4bit: bool = True
    
    # LoRA Ayarları
    r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    target_modules: list = field(default_factory=lambda: [
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj",
    ])
    
    # Eğitim Hiperparametreleri
    batch_size: int = 2
    gradient_accumulation_steps: int = 4
    learning_rate: float = 2e-4
    max_steps: int = 100
    logging_steps: int = 10
    optimizer: str = "adamw_8bit"
    weight_decay: float = 0.01
    lr_scheduler_type: str = "linear"
    seed: int = 42

    # Veri Yolu
    output_dir: str = "training/outputs"
    dataset_path: str = "training/dataset/sft_train.jsonl"
