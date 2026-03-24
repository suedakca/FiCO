# FiCo Kaşif: Teknik Mimari Dokümanı (v1.0)

## 1. Giriş
FiCo Kaşif, katılım bankacılığı prensipleri, AAOIFI standartları ve iç mevzuat verilerini kullanarak, ürün yöneticileri ve operasyon ekiplerine saniyeler içinde doğrulanmış, kaynak atıflı cevaplar sunan bir **Retrieval-Augmented Generation (RAG)** sistemidir. Projenin amacı, manuel uyum kontrol süreçlerini otomatize etmek ve karar destek mekanizması olarak hizmet vermektir.

## 2. Teknoloji Yığını (Tech Stack)

| Bileşen | Seçilen Teknoloji | Gerekçe |
| :--- | :--- | :--- |
| **Dil Modeli (LLM)** | GPT-4o veya Claude 3.5 Sonnet | Karmaşık finansal ve hukuki metinleri anlama ve akıl yürütme kapasitesi. |
| **Orchestration** | LangChain veya LlamaIndex | Veri boru hatları (pipelines) ve RAG akışlarını yönetmek için standart kütüphaneler. |
| **Vektör Veritabanı** | Pinecone veya Weaviate | Yüksek boyutlu gömmelerin (embeddings) hızlı ve ölçeklenebilir aranması. |
| **Backend** | Python (FastAPI) | LLM ekosistemiyle uyum ve asenkron işlem desteği. |
| **Frontend** | React.js + Tailwind CSS | Hızlı arayüz geliştirme ve kullanıcı dostu chat deneyimi. |
| **Embedding Modeli** | text-embedding-3-small | Türkçe finansal terminolojiyi temsil yeteneği ve maliyet etkinliği. |

## 3. Sistem Mimarisi

### Yüksek Seviye Görünüm
Sistem, kullanıcıdan gelen doğal dil sorgusunu alan bir istemci ve bu sorguyu anlamlandırıp bilgi havuzundan ilgili parçaları çeken bir RAG motorundan oluşur.

### Mimari Modeller
* **RAG Pattern:** Veri "halüsinasyonunu" önlemek için sadece belirli dokümanlar (AAOIFI, BDDK, İç Arşiv) üzerinden cevap üretilir.
* **Human-in-the-loop (HITL):** Güven skoru belirli bir eşiğin altındaki cevaplar, onay için uzman havuzuna (Danışma Komitesi ekranına) düşer.

## 4. Veri Mimarisi

### Veri İşleme Akışı (Ingestion Pipeline)
1.  **Parsing:** PDF/HTML formatındaki mevzuat metinleri metne dönüştürülür.
2.  **Chunking:** Metinler, anlamsal bütünlüğü bozmayacak şekilde (örn: 500 token + 50 token overlap) parçalara ayrılır.
3.  **Embedding:** Parçalar vektörlere dönüştürülür.
4.  **Metadata Tagging:** Her vektöre kaynak (örn: "AAOIFI Standart No: 5", "BDDK Karar Tarihi: 2024") etiketi eklenir.

### Veritabanı Şeması (İlişkisel Kısım)
Vektör tabanının yanı sıra, kullanıcı geçmişi ve geri bildirimleri için bir PostgreSQL şeması kullanılır:
* `Queries`: query_id, user_id, timestamp, query_text
* `Responses`: response_id, query_id, answer_text, source_urls, confidence_score
* `Feedbacks`: feedback_id, response_id, rating (1-5), comments

## 5. API Tasarımı (RESTful)

### Temel Endpointler
* `POST /v1/query`: Kullanıcı sorusunu alır, RAG sürecini başlatır ve cevabı döner.
    * *Payload:* `{ "user_id": "string", "text": "string" }`
* `GET /v1/sources/{source_id}`: Cevapta atıf yapılan orijinal doküman parçasını getirir.
* `POST /v1/feedback`: Kullanıcının cevabı puanlamasını sağlar (Sistemi iyileştirmek için).

## 6. Güvenlik ve Uyumluluk
* **Kimlik Doğrulama:** Keycloak veya Azure AD entegrasyonu (OAuth2).
* **Veri Gizliliği:** Kişisel Verilerin Korunması Kanunu (KVKK) uyarınca, LLM'e gönderilmeden önce sorgulardaki hassas veriler (Pİİ) maskelenir.
* **Encryption:** Veriler hem iletim sırasında (TLS 1.3) hem de bekleme durumunda (AES-256) şifrelenir.

## 7. Dağıtım Stratejisi (Deployment)
* **Containerization:** Uygulama Dockerize edilerek her ortamda tutarlılık sağlanır.
* **CI/CD:** GitHub Actions üzerinden otomatik test ve dağıtım süreçleri yönetilir.
* **Hosting:** Banka politikalarına göre On-premise OpenShift veya Azure Kubernetes Service (AKS).

## 8. İzleme ve Kayıt (Monitoring)
* **LangSmith:** LLM çağrılarının takibi, maliyet analizi ve prompt performans izleme.
* **Prometheus & Grafana:** Sistem sağlığı (CPU, RAM) ve API yanıt sürelerinin izlenmesi.
* **ELK Stack:** Tüm uygulama loglarının merkezi yönetimi.
