# FiCO — Fıkhi Uyum Analisti

Katılım bankacılığı mevzuatları (AAOIFI / TKBB) üzerinde yerel LLM ile çalışan yapay zeka destekli uyum danışmanı.

**Mimari:** React 19 + FastAPI + ChromaDB + Ollama (yerel model, internet bağlantısı gerekmez)

---

## Gereksinimler

| Araç | Sürüm | Notlar |
|------|-------|--------|
| Python | 3.9+ | Backend için |
| Node.js | 18+ | Frontend için |
| [Ollama](https://ollama.com) | güncel | Yerel LLM çalıştırıcı |
| PostgreSQL | 14+ | Sorgu geçmişi — **opsiyonel** |

---

## Kurulum

### 1. Ollama — Modelleri İndir

```bash
# Ana LLM (Türkçe ince ayarlı Gemma 9B)
ollama pull bazobehram/turkish-gemma-9b-t1

# Embedding modeli
ollama pull nomic-embed-text
```

Modellerin indirildiğini doğrula:
```bash
ollama list
```

Ollama servisini başlat (yeni bir terminalde açık bırak):
```bash
ollama serve
# Çalışıyor: http://localhost:11434
```

---

### 2. Backend

```bash
cd backend

# Sanal ortam oluştur (önerilir)
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Bağımlılıkları yükle
pip install -r requirements.txt
```

#### Ortam Değişkenleri

Proje kökünde `.env` dosyası oluştur (PostgreSQL olmadan da çalışır):

```env
# PostgreSQL — opsiyonel, kapalıysa geçmiş RAM'de tutulmaz, hata vermez
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=fico_kasif
```

#### Bilgi Tabanını Başlat (Sadece ilk kurulumda)

```bash
# backend klasöründeyken çalıştır
python3 scripts/init_chroma.py
```

Bu komut `data/knowledge_base.json` dosyasını okuyarak `data/chroma_db/` dizinini oluşturur. Bir kez çalıştırman yeterli.

#### Backend'i Başlat

```bash
python3 -m uvicorn main:app --reload --reload-exclude ".venv" --port 8000
```

- API: [http://localhost:8000](http://localhost:8000)
- Swagger: [http://localhost:8000/v1/openapi.json](http://localhost:8000/v1/openapi.json)

---

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Uygulama: [http://localhost:5173](http://localhost:5173)

---

## Tam Başlatma Sırası (Özet)

```bash
# Terminal 1 — Ollama
ollama serve

# Terminal 2 — Backend
cd backend && source .venv/bin/activate && python3 -m uvicorn main:app --reload --reload-exclude ".venv" --port 8000

# Terminal 3 — Frontend
cd frontend && npm run dev
```

Tarayıcıda [http://localhost:5173](http://localhost:5173) adresini aç.

---

## Proje Yapısı

```
FiCO/
├── backend/
│   ├── api/v1/endpoints/
│   │   └── query.py              # Sorgu endpoint'i (POST /v1/query)
│   ├── core/
│   │   ├── config.py             # Uygulama ayarları (.env okur)
│   │   └── db.py                 # Veritabanı bağlantısı
│   ├── data/
│   │   ├── knowledge_base.json   # Mevzuat bilgi tabanı (kaynak)
│   │   └── chroma_db/            # Vektör DB — init_chroma.py ile oluşur
│   ├── models/
│   │   ├── database.py           # SQLAlchemy tabloları
│   │   └── schemas.py            # Pydantic şemaları
│   ├── scripts/
│   │   └── init_chroma.py        # Bilgi tabanı başlatma (bir kez çalıştır)
│   ├── services/
│   │   ├── rag_service.py        # ReAct ajan döngüsü (ana mantık)
│   │   ├── chroma_service.py     # Hibrit arama: Vector + BM25 + Cross-Encoder
│   │   ├── evaluation_service.py # RAGAS benzeri metrikler (sadakat, uygunluk)
│   │   └── agent_tools.py        # Belge getirme ve uyum doğrulama araçları
│   ├── main.py                   # FastAPI giriş noktası
│   └── requirements.txt
└── frontend/
    └── src/
        └── App.jsx               # Ana React bileşeni
```

---

## API Endpointleri

| Method | Endpoint | Açıklama |
|--------|----------|----------|
| `POST` | `/v1/query` | Uyum analizi yap, cevap döner |
| `GET` | `/v1/query?user_id=demo_user` | Sorgu geçmişini getir |
| `POST` | `/v1/query/stream` | Streaming (akan) cevap |

**Örnek istek:**
```bash
curl -X POST http://localhost:8000/v1/query \
  -H "Content-Type: application/json" \
  -d '{"user_id": "demo_user", "query_text": "Mudaraba sözleşmesinde zarar kime aittir?"}'
```

---

## Sorun Giderme

**Ollama modeli bulunamıyor:**
```bash
ollama pull bazobehram/turkish-gemma-9b-t1
ollama pull nomic-embed-text
```

**ChromaDB boş, yanıt "İlgili bilgi bulunamadı" diyor:**
```bash
cd backend && python3 scripts/init_chroma.py
```

**PostgreSQL bağlantı hatası:**
Uygulama DB olmadan çalışmaya devam eder — sorgu geçmişi kaydedilmez ama hata üretmez. Tamamen devre dışı bırakmak için `.env` dosyasındaki `POSTGRES_*` satırlarını sil.

**`react-markdown` modülü bulunamıyor:**
```bash
cd frontend && npm install react-markdown
```

**500 Internal Server Error (sunucu kapatılırken):**
CTRL+C ile sunucu kapatıldığında aktif istek varsa bu hata normaldir, kod hatası değildir.
