import torch
from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
from trl import SFTTrainer
from peft import LoraConfig, get_peft_model
import os

def run_sanity_training():
    print("🚀 Starting FiCO Sanity Training Validation...")
    
    # Tiny model for validation (Fast and No memory issues)
    model_id = "facebook/opt-125m" 
    dataset_path = "backend/ml/dataset/sft_train.json"
    
    if not os.path.exists(dataset_path):
        print(f"❌ Error: Dataset not found at {dataset_path}")
        return

    # 1. Load data
    dataset = load_dataset("json", data_files=dataset_path, split="train[:10]") # Use 10 samples
    
    # 2. Load Model & Tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    tokenizer.pad_token = tokenizer.eos_token
    
    model = AutoModelForCausalLM.from_pretrained(
        model_id, 
        device_map="auto" if torch.backends.mps.is_available() else "cpu"
    )

    # 3. LoRA Configuration
    peft_config = LoraConfig(
        r=8,
        lora_alpha=16,
        target_modules=["q_proj", "v_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, peft_config)

    # 4. Training Arguments (Minimal)
    training_args = TrainingArguments(
        output_dir="./backend/ml/sanity_outputs",
        max_steps=3, # Only 3 steps for sanity
        per_device_train_batch_size=1,
        learning_rate=2e-4,
        logging_steps=1,
        report_to="none"
    )

    # 5. Trainer
    trainer = SFTTrainer(
        model=model,
        train_dataset=dataset,
        max_seq_length=128,
        args=training_args,
    )

    # 6. Execute
    print("📊 Executing 3 steps of training...")
    trainer.train()
    print("✅ Sanity Training Success! The pipeline is fully functional.")

if __name__ == "__main__":
    run_sanity_training()
