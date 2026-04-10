# FiCO - Katılım Bankacılığı Uyum Analisti

FiCO, Katılım Bankacılığı (AAOIFI, TKBB) prensiplerine %100 uyumla çalışan, gelişmiş bir fıkhi denetim ve analiz ajansıdır. Sadece bilgi sağlamakla kalmaz, aynı zamanda ReAct akıl yürütme döngüsü ile belgeleri tarar, kaynakları doğrular ve tutarlılık analizi yapar.

## 🚀 Gelişmiş Özellikler (Ajan Yapısı)

- **ReAct Agent Döngüsü**: Ajan, her soruda `Düşünce -> Eylem -> Gözlem` döngüsünü takip ederek derinlemesine analiz yapar.
- **Hibrit Arama (Hybrid Search)**: ChromaDB (Vektör) ve BM25 (Anahtar Kelime) tekniklerini birleştirerek en alakalı mevzuat parçalarını bulur.
- **Uyum Doğrulayıcı (Compliance Validator)**: Üretilen cevapların kaynak metne sadık olup olmadığını otomatik olarak denetler (Anti-Hallucination).
- **Mevzuat Birleştirici (Policy Aggregator)**: AAOIFI, TKBB ve Kurum İçi Fetvalar gibi farklı kaynakları kategori bazlı hiyerarşik olarak birleştirir.
- **Dinamik Yönlendirme (Routing)**: Soruları karmaşıklığına göre sınıflandırarak (Hızlı RAG vs. Çok Adımlı Akıl Yürütme) en uygun yanıt stratejisini belirler.
- **Kalıcı Hafıza**: `SQLAlchemyChatMessageHistory` ile kullanıcıyla olan geçmiş konuşmaları hatırlar ve bağlamı korur.

## 🛠️ Kurulum ve Çalıştırma

### Ön Gereksinimler
- Python 3.9+
- Node.js 18+
- **Ollama**: Yerel modelleri (Llama 3.2, Nomic-Embed-Text) çalıştırmak için gereklidir.

### Hızlı Başlat

1. **Bağımlılıkları Yükleyin**:
   ```bash
   npm install && npm run install:all
   ```

2. **Ollama Servisini Başlatın**:
   Terminalde `ollama serve` komutunu çalıştırın ve gerekli modellerin yüklü olduğundan emin olun:
   ```bash
   ollama pull llama3.2
   ollama pull nomic-embed-text
   ```

3. **Vektör Veritabanını İlklendirin**:
   Mevcut bilgi tabanını ChromaDB'ye aktarmak için:
   ```bash
   python3 backend/scripts/init_chroma.py
   ```

4. **Uygulamayı Çalıştırın**:
   ```bash
   npm run dev
   ```

5. **Ollama Servisini Durdurun**:
   ```bash
   pkill ollama
   ```

## 📂 Proje Yapısı

```
FiCO/
├── backend/              # FastAPI & Agentic Backend
│   ├── api/              # API Endpoints
│   ├── core/             # Konfigürasyon ve DB Ayarları
│   ├── data/             # Bilgi Tabanı ve ChromaDB Dosyaları
│   ├── models/           # SQLAlchemy & Veri Modelleri
│   ├── services/         # Ajan Mantığı (ReAct, Hybrid Search, Tools)
│   │   ├── agent_tools.py      # Ajan Araçları
│   │   ├── chroma_service.py   # Hibrit Arama Servisi
│   │   ├── rag_service.py      # ReAct Agent & Core
│   │   └── evaluation_service.py # RAGAS Metrikleri
│   └── scripts/          # Veri Yönetim Betikleri
├── frontend/             # React (Vite) Frontend
└── README.md
```

## 🤝 Katkıda Bulunma

Katılım Bankacılığı kurallarını ve dijital uyumu ileriye taşımak için katkılarınızı bekliyoruz! Lütfen bir issue açın veya doğrudan bir pull request gönderin.