# NOTE: Bu script Unsloth kütüphanesi kurulu olan bir GPU ortamında çalıştırılmalıdır.
import os
import torch
from unsloth import FastLanguageModel
from datasets import load_dataset
from trl import SFTTrainer
from transformers import TrainingArguments
from training.config import TrainingConfig

def train_fico_model():
    config = TrainingConfig()
    
    # 1. Modeli ve Tokenizer'ı Yükle
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name = config.model_name,
        max_seq_length = config.max_seq_length,
        load_in_4bit = config.load_in_4bit,
    )

    # 2. LoRA Adapter Ayarlarını Yap
    model = FastLanguageModel.get_peft_model(
        model,
        r = config.r,
        target_modules = ["q_proj", "k_proj", "v_proj", "o_proj",
                      "gate_proj", "up_proj", "down_proj",],
        lora_alpha = 32,
        lora_dropout = 0.05,
        bias = "none",
        use_gradient_checkpointing = True,
        random_state = 42,
    )

    # 3. Veri Setini Hazırla
    # SFT formatına uygun bir prompt şablonu kullanıyoruz
    alpaca_prompt = """Aşağıda bir görevi tanımlayan bir talimat ve bağlam bulunmaktadır. İsteği uygun şekilde tamamlayan bir yanıt yazın.

### Talimat:
{}

### Bağlam:
{}

### Yanıt:
{}"""

    def formatting_prompts_func(examples):
        instructions = examples["instruction"]
        contexts     = examples["context"]
        outputs      = examples["response"]
        texts = []
        for instruction, context, output in zip(instructions, contexts, outputs):
            text = alpaca_prompt.format(instruction, context, output)
            texts.append(text)
        return { "text" : texts, }

    dataset = load_dataset("json", data_files = config.dataset_path, split = "train")
    dataset = dataset.map(formatting_prompts_func, batched = True)

    # 4. Trainer'ı Başlat
    trainer = SFTTrainer(
        model = model,
        train_dataset = dataset,
        dataset_text_field = "text",
        max_seq_length = config.max_seq_length,
        args = TrainingArguments(
            per_device_train_batch_size = config.batch_size,
            gradient_accumulation_steps = config.gradient_accumulation_steps,
            warmup_steps = 5,
            max_steps = config.max_steps,
            learning_rate = config.learning_rate,
            fp16 = not torch.cuda.is_bf16_supported(),
            bf16 = torch.cuda.is_bf16_supported(),
            logging_steps = config.logging_steps,
            optim = config.optimizer,
            weight_decay = config.weight_decay,
            lr_scheduler_type = config.lr_scheduler_type,
            seed = config.seed,
            output_dir = config.output_dir,
        ),
    )

    # 5. Eğitimi Başlat
    trainer.train()

    # 6. Modeli Kaydet
    model.save_pretrained("./training/outputs/fico_adapter")
    tokenizer.save_pretrained("./training/outputs/fico_adapter")
    print("✅ Eğitim tamamlandı ve adapter kaydedildi.")

if __name__ == "__main__":
    train_fico_model()
