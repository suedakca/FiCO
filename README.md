# FiCO - Katılım Bankacılığı Uyum Asistanı

FiCO, katılım bankacılığı sektöründeki finansal işlemlerin İslami finans prensiplerine (Sharia) uygunluğunu denetlemek ve analiz etmek için tasarlanmış yapay zeka destekli bir uyum asistanıdır.

## 🚀 Özellikler

- **RAG (Retrieval-Augmented Generation):** AAOIFI standartları ve kurum içi fetvalar ile eğitilmiş bilgi tabanı üzerinden doğru ve kaynak gösteren cevaplar üretir.
- **Akıllı Soru Önerileri:** Kullanıcının ihtiyacına yönelik örnek sorular sunarak keşfi kolaylaştırır.
- **Güven Skoru:** Üretilen cevabın bilgi tabanına ne kadar uygun olduğunu yüzde olarak gösterir.
- **Sohbet Geçmişi:** Tüm konuşmaları kaydeder ve analiz eder.

## 🛠️ Kurulum ve Çalıştırma

### Ön Gereksinimler
- Python 3.8+
- Node.js 16+
- OpenAI API Key (.env dosyasına eklenmeli)

### Hızlı Başlat (Önerilen)

Tüm sistemi (Backend + Frontend) tek bir komutla başlatabilirsiniz:

1. Gerekli kütüphaneleri yükleyin (tek seferlik):
   ```bash
   npm install && npm run install:all
   ```

2. Uygulamayı çalıştırın:
   ```bash
   npm run dev
   ```

Bu komut hem FastAPI'yi (Port 8000) hem de Vite'yi (Port 5173) aynı anda ayağa kaldıracaktır.

---

### Manuel Başlatma (Ayrı Ayrı)
Alternatif olarak, servisleri ayrı terminallerde de çalıştırabilirsiniz:

Uygulamaya `http://localhost:5173` adresinden erişebilirsiniz.

## 📂 Proje Yapısı

```
FiCO/
├── backend/              # FastAPI Backend
│   ├── api/              # API Endpoints
│   ├── core/             # Konfigürasyon ve Veritabanı
│   ├── data/             # Bilgi Tabanı (JSON)
│   ├── models/           # SQLAlchemy Modelleri
│   ├── services/         # İş Mantığı (RAG Service)
│   └── main.py           # Uygulama Başlangıç Noktası
├── frontend/             # React Frontend
│   ├── src/
│   │   ├── components/   # UI Bileşenleri
│   │   ├── services/     # API Servisleri
│   │   └── App.jsx       # Ana Uygulama
│   └── package.json
└── README.md
```

## 🤝 Katkıda Bulunma

Katkılarınız için teşekkürler! Lütfen bir issue açın veya doğrudan bir pull request gönderin.