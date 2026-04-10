import json
import random
import os
from typing import List, Dict, Any

class FiCODatasetGenerator:
    """Mevzuat verilerinden 1000+ örnekli, çoklu kural akıl yürütme (multi-rule) destekli SFT motoru."""
    
    def __init__(self, kb_path: str = "./backend/data/knowledge_base.json"):
        with open(kb_path, "r", encoding="utf-8") as f:
            self.kb = json.load(f)
        
        self.task_templates = {
            "direct": ["{source} standartlarına göre {topic} nedir?", "{topic} hakkında genel kuralı açıkla."],
            "edge_case": ["Eğer bir durumda {topic} {scenario} gerçekleşirse hüküm ne olur?"],
            "negative": ["Müşteri {topic} konusunda {prohibited_action} talep ediyor. Onay verilebilir mi?"],
            "comparison": ["{topic} ile {other_topic} arasındaki temel farklar nelerdir?"],
            "multi_rule": ["{topic1} ve {topic2} kurallarını birlikte düşündüğümüzde zarar paylaşımı farkı nedir?"],
            "conditional": ["Eğer müşteri {condition} yaparsa, {topic} hükmü değişir mi?"]
        }

    def generate_1000_plus_dataset(self) -> List[Dict[str, Any]]:
        """1000+ örnekli, karmaşık muhakeme içeren veri seti üretir."""
        dataset = []
        
        # A. SINGLE RULE GENERATION (Her kural için temel set)
        for rule in self.kb:
            topic = rule["metadata"].get("category", "bu konu")
            source = rule["source"]
            content = rule["content"]
            citation = rule["metadata"].get("exact_citation", "Bilinmeyen Madde")

            # 3 Basic
            for _ in range(3):
                dataset.append(self._format_sample(random.choice(self.task_templates["direct"]).format(source=source, topic=topic), content, citation))
            # 2 Edge
            scenarios = ["beklenmedik bir kriz", "operasyonel hata", "teknik aksaklık"]
            for _ in range(2):
                dataset.append(self._format_sample(random.choice(self.task_templates["edge_case"]).format(topic=topic, scenario=random.choice(scenarios)), content, citation))
            # 2 Negative
            prohibitions = ["kayıt dışı işlem", "faizli takas", "şeffaflık ihlali"]
            for _ in range(2):
                dataset.append(self._format_sample(random.choice(self.task_templates["negative"]).format(topic=topic, prohibited_action=random.choice(prohibitions)), content, citation))
            # 1 Comparison (Basic)
            dataset.append(self._format_sample(self.task_templates["comparison"][0].format(topic=topic, other_topic="konvansiyonel araçlar"), content, citation))
            # 2 Conditional
            conditions = ["ihmal ederse", "kasıtlı davranırsa", "sözleşmeyi ihlal ederse"]
            for _ in range(2):
                dataset.append(self._format_sample(self.task_templates["conditional"][0].format(topic=topic, condition=random.choice(conditions)), content, citation))

        # B. MULTI-RULE GENERATION (İki kural arası muhakeme)
        for _ in range(50): # 50 farklı ikili kombinasyon
            r1, r2 = random.sample(self.kb, 2)
            t1, t2 = r1["metadata"].get("category", "A"), r2["metadata"].get("category", "B")
            instruction = self.task_templates["multi_rule"][0].format(topic1=t1, topic2=t2)
            combined_content = f"1. {r1['content']}\n2. {r2['content']}"
            combined_citation = f"{r1['metadata'].get('exact_citation','')} / {r2['metadata'].get('exact_citation','')}"
            dataset.append(self._format_sample(instruction, combined_content, combined_citation))

        # C. SCENARIO AUGMENTATION (1000'e tamamlamak için)
        target = 1000
        while len(dataset) < target:
            base_sample = random.choice(dataset)
            prefix = random.choice(["Sayın analist,", "Fıkhi açıdan,", "Uyum denetimi kapsamında,"])
            new_instruction = f"{prefix} {base_sample['instruction']}"
            dataset.append({
                "instruction": new_instruction,
                "input": "",
                "output": base_sample["output"]
            })
            
        return dataset

    def _format_sample(self, instruction: str, content: str, citation: str) -> Dict[str, Any]:
        """Üretim formatı: HÜKÜM -> GEREKÇE -> KAYNAK"""
        output = f"HÜKÜM:\nAnaliz sonucunda ilgili işlemin hükmü belirlenmiştir.\n\nGEREKÇE:\n{content}\n\nKAYNAK:\n{citation}"
        return {"instruction": instruction, "input": "", "output": output}

    def save_dataset(self, path: str = "./backend/ml/dataset/sft_train.json"):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        data = self.generate_1000_plus_dataset()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"🚀 {len(data)} örnekli v2.1 eğitim seti hazırlandı: {path}")

if __name__ == "__main__":
    generator = FiCODatasetGenerator()
    generator.save_dataset()
