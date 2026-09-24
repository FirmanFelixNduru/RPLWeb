# CompareBuy 📱⚡
> **Platform Cerdas Perbandingan & Rekomendasi Perangkat Teknologi**  
> *Membantu konsumen cerdas mengatasi "Analysis Paralysis", menyaring ulasan palsu, dan menemukan gadget paling worth-it dengan Dynamic Scoring Engine & Live Marketplace Scraping.*

---

## 📌 Daftar Isi
1. [Tentang CompareBuy](#-tentang-comparebuy)
2. [Latar Belakang & Masalah](#-latar-belakang--masalah)
3. [Fitur-Fitur Utama](#-fitur-fitur-utama)
4. [Arsitektur & Tech Stack](#-arsitektur--tech-stack)
5. [Struktur Direktori Proyek](#-struktur-direktori-proyek)
6. [Panduan Instalasi & Menjalankan Lokal](#-panduan-instalasi--menjalankan-lokal)
   - [Persyaratan Sistem](#persyaratan-sistem)
   - [Langkah 1: Setup Backend (FastAPI)](#langkah-1-setup-backend-fastapi)
   - [Langkah 2: Setup Frontend (Next.js)](#langkah-2-setup-frontend-nextjs)
7. [Dokumentasi API Endpoint](#-dokumentasi-api-endpoint)
8. [Algoritma Scoring Engine (MCDA)](#-algoritma-scoring-engine-mcda)
9. [Scraping Harga Marketplace Live](#-scraping-harga-marketplace-live)
10. [Panduan Deployment ke Cloud (Vercel & Render/Railway)](#-panduan-deployment-ke-cloud)
11. [Lisensi & Kontribusi](#-lisensi--kontribusi)

---

## 💡 Tentang CompareBuy

**CompareBuy** adalah platform web modern *full-stack* yang menyajikan ekosistem evaluasi gadget secara objektif dan matematis. Melalui kombinasi **Frontend Next.js (App Router)** dan **Backend Python FastAPI Microservice**, platform ini memecahkan kerumitan memilih perangkat teknologi (Smartphone, Laptop, Tablet, TWS, Smartwatch) di pasar Indonesia.

Aplikasi ini dirancang *production-ready* dengan dukungan *zero-config deployment* ke **Vercel** untuk Frontend dan *containerized deployment* (**Docker / Procfile / railway.json**) ke **Render** atau **Railway** untuk Backend.

---

## 🎯 Latar Belakang & Masalah

Konsumen modern sering mengalami hambatan kritis saat hendak membeli perangkat teknologi:
1. **Analysis Paralysis**: Tersedia ratusan model gadget dengan lembar spesifikasi teknis yang membingungkan orang awam.
2. **Ulasan Palsu & Bias Promosi**: Banyak ulasan di media sosial disponsori merek tanpa mengungkap kekurangan riil produk.
3. **Ketidakpastian Purna Jual & Garansi**: Jarang ada platform yang menyajikan transparansi durasi garansi resmi, ketersediaan pusat servis, dan kemudahan proses klaim.
4. **Disparitas Harga Marketplace**: Harga satu produk di Tokopedia, Shopee, dan Lazada sering berbeda jauh dengan ribuan penjual yang membingungkan.

**Solusi CompareBuy**: Mengintegrasikan algoritma rekomendasi terbobot (*Multi-Criteria Decision Analysis*), agregator sentimen komunitas terverifikasi, indeks transparansi garansi, serta pemantauan harga *real-time* lintas *marketplace*.

---

## ✨ Fitur-Fitur Utama

| No | Fitur | Deskripsi |
|---|---|---|
| 1 | **Smart Recommendation Wizard** | Panduan 4 langkah interaktif: Kategori → Budget → Skenario Penggunaan → Prioritas Trade-Off. |
| 2 | **Weighted Dynamic Scoring Engine** | Mesin kalkulasi di FastAPI yang menghitung skor personal (0-100) dan menyajikan narasi kontekstual *"Why This Product?"*. |
| 3 | **Side-by-Side Comparison Matrix** | Matriks multi-produk (hingga 4 gadget) dengan **Auto-Highlighting** visual otomatis pada spesifikasi paling unggul di setiap baris. |
| 4 | **Floating Comparison Dock** | *Dock* melayang di bagian bawah layar untuk menyimpan, menghapus, dan membandingkan produk dari katalog secara instan. |
| 5 | **Real User Sentiment Aggregator** | Ringkasan sentimen AI yang merangkum kelebihan dan kekurangan asli dari ribuan ulasan komunitas bebas bias. |
| 6 | **After-Sales & Warranty Index** | Skor transparansi purna jual: durasi garansi resmi, kemudahan klaim (skala 1-10), dan sebaran *service center* resmi di Indonesia. |
| 7 | **Curated Product Catalog** | Katalog gadget terkurasi dengan pencarian instan (*instant search*), filter multi-tag (kategori, brand, budget), dan pengurutan dinamis. |
| 8 | **Modal Rincian Produk Multi-Tab** | Modal interaktif 4 tab: Spesifikasi Teknis, User Experience & Review, Garansi & Purna Jual, serta Marketplace Live & Value. |
| 9 | **Dark Mode / Light Mode** | Dukungan tema gelap dan terang dengan transisi CSS halus serta persistensi status di `localStorage`. |
| 10 | **Live Marketplace Price Scraping** | Layanan backend yang memindai harga *real-time* dari **Tokopedia**, **Shopee**, dan **Lazada** lengkap dengan tautan toko resmi/afiliasi. |

---

## 🛠️ Arsitektur & Tech Stack

```
┌────────────────────────────────┐         REST API (JSON)         ┌────────────────────────────────┐
│   Frontend (Next.js 14)        │ ◄─────────────────────────────► │   Backend (FastAPI Python)     │
│   • React 18 & App Router      │                                 │   • Python 3.12 / 3.13         │
│   • Tailwind CSS (Dark/Light)  │                                 │   • Pydantic V2 Schemas        │
│   • Lucide React Icons         │                                 │   • MCDA Dynamic Scoring       │
│   • Resilient Client Fallback  │                                 │   • Httpx + BeautifulSoup4     │
└────────────────────────────────┘                                 └────────────────────────────────┘
                 │                                                                  │
                 ▼                                                                  ▼
        Deploy to VERCEL                                                Deploy to RENDER / RAILWAY
```

* **Frontend**: Next.js 14 (App Router), React 18, Tailwind CSS, Lucide Icons.
* **Backend**: Python 3.12+, FastAPI, Uvicorn, Pydantic V2, Httpx, BeautifulSoup4.
* **Deployment Tools**: Dockerfile (Multi-Stage), Procfile, railway.json, next.config.js.

---

## 📂 Struktur Direktori Proyek

```
Rekayasa Perangkat Lunak/
├── backend/                             # Python FastAPI Microservice
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                      # Entry point FastAPI, CORS, & Lifespan
│   │   ├── models.py                    # Schema Pydantic lengkap
│   │   ├── products.py                  # Database 20 produk terkurasi pasar Indonesia
│   │   ├── scoring.py                   # Weighted Dynamic Scoring Engine (MCDA)
│   │   ├── scraper.py                   # Scraper Tokopedia, Shopee, Lazada + Fallback
│   │   └── routers/
│   │       ├── __init__.py
│   │       ├── catalog.py               # Endpoint /api/products, brands, categories
│   │       ├── scoring.py               # Endpoint /api/score
│   │       ├── compare.py               # Endpoint /api/compare (Auto-Highlighting)
│   │       └── prices.py                # Endpoint /api/prices/{id}
│   ├── Dockerfile                       # Multi-stage production container
│   ├── Procfile                         # Konfigurasi deployment Render
│   ├── railway.json                     # Konfigurasi deployment Railway
│   ├── requirements.txt                 # Dependensi Python
│   └── .env.example                     # Templat environment variable backend
│
├── frontend/                            # Next.js App Router Frontend
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.js                # Root layout, ThemeProvider, Dock & Modal
│   │   │   ├── page.js                  # Landing page interaktif & Hero
│   │   │   ├── globals.css              # Variabel Tailwind & transisi dark mode
│   │   │   ├── catalog/page.js          # Halaman Katalog Gadget Terkurasi
│   │   │   ├── compare/page.js          # Halaman Matriks Komparasi Side-by-Side
│   │   │   └── wizard/page.js           # Halaman Smart Recommendation Wizard
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── Navbar.js            # Navigasi responsif & drawer mobile
│   │   │   │   ├── Footer.js            # Footer ekosistem & info platform
│   │   │   │   └── FloatingDock.js      # Dock perbandingan melayang di bawah layar
│   │   │   ├── catalog/
│   │   │   │   ├── ProductCard.js       # Kartu produk dengan badge & tombol aksi
│   │   │   │   ├── SearchBar.js         # Input pencarian instan
│   │   │   │   └── FilterPanel.js       # Panel filter multi-tag & pengurutan
│   │   │   ├── wizard/
│   │   │   │   ├── StepCategory.js      # Langkah 1: Kategori
│   │   │   │   ├── StepBudget.js        # Langkah 2: Slider rentang anggaran & preset
│   │   │   │   ├── StepScenario.js      # Langkah 3: Skenario aktivitas harian
│   │   │   │   ├── StepPriority.js      # Langkah 4: Slider trade-off prioritas (1-5)
│   │   │   │   └── WizardResults.js     # Tampilan hasil ranking & narasi "Why This Product"
│   │   │   ├── compare/
│   │   │   │   └── ComparisonMatrix.js  # Tabel matriks komparasi + Auto-Highlight
│   │   │   ├── product/
│   │   │   │   ├── ProductModal.js      # Modal utama 4 tab
│   │   │   │   ├── TabSpecs.js          # Tab 1: Spesifikasi teknis
│   │   │   │   ├── TabReviews.js        # Tab 2: Real User Sentiment Aggregator
│   │   │   │   ├── TabWarranty.js       # Tab 3: After-Sales & Warranty Index
│   │   │   │   └── TabValue.js          # Tab 4: Live Marketplace Pricing (Tokopedia/Shopee/Lazada)
│   │   │   └── ui/
│   │   │       ├── ThemeToggle.js       # Tombol pengubah Dark/Light mode
│   │   │       ├── ScoreBadge.js        # Lencana skor dinamis bergradien warna
│   │   │       └── PriceTag.js          # Format mata uang Rupiah Indonesia
│   │   ├── context/
│   │   │   ├── ThemeContext.js          # State tema & persistensi localStorage
│   │   │   └── CompareContext.js        # State dock komparasi & modal produk
│   │   ├── data/
│   │   │   └── products.js              # Seed data fallback frontend
│   │   └── lib/
│   │       └── api.js                   # Klien API HTTP + fallback cerdas
│   ├── next.config.js                   # Konfigurasi Next.js
│   ├── tailwind.config.js               # Konfigurasi Tailwind & tema kustom
│   ├── postcss.config.js
│   ├── package.json
│   └── .env.example                     # NEXT_PUBLIC_API_URL
│
└── README.md                            # Dokumentasi lengkap proyek
```

---

## 🚀 Panduan Instalasi & Menjalankan Lokal

### Persyaratan Sistem
* **Node.js**: v18.x atau v20.x atau lebih baru
* **npm**: v9.x atau lebih baru
* **Python**: v3.10 atau v3.11 atau v3.12+

---

### Langkah 1: Setup Backend (FastAPI)

1. Buka terminal dan masuk ke direktori `backend/`:
   ```bash
   cd backend
   ```

2. Buat dan aktifkan *virtual environment* Python (opsional namun disarankan):
   ```bash
   # Windows (PowerShell)
   python -m venv venv
   .\venv\Scripts\Activate.ps1

   # Linux / macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Pasang semua dependensi:
   ```bash
   pip install -r requirements.txt
   ```

4. Buat file `.env` dari templat:
   ```bash
   cp .env.example .env
   ```

5. Jalankan server FastAPI dengan Uvicorn:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
   * Server backend aktif di: `http://localhost:8000`
   * Dokumentasi Swagger interaktif: `http://localhost:8000/docs`
   * Dokumentasi ReDoc: `http://localhost:8000/redoc`

---

### Langkah 2: Setup Frontend (Next.js)

1. Buka terminal baru dan masuk ke direktori `frontend/`:
   ```bash
   cd frontend
   ```

2. Pasang semua dependensi Node.js:
   ```bash
   npm install
   ```

3. Buat file `.env.local` dari templat:
   ```bash
   cp .env.example .env.local
   ```
   *Pastikan isinya mengarah ke backend lokal:*
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

4. Jalankan server pengembangan Next.js:
   ```bash
   npm run dev
   ```
   * Aplikasi frontend aktif di: `http://localhost:3000`

---

## 📡 Dokumentasi API Endpoint

Backend FastAPI menyediakan endpoint RESTful yang siap dikonsumsi:

| Method | Endpoint | Deskripsi |
|---|---|---|
| `GET` | `/` | Status layanan & versi API |
| `GET` | `/health` | Healthcheck endpoint untuk Docker / Railway / Render |
| `GET` | `/api/products` | Mengambil seluruh katalog produk dengan query parameter: `search`, `category`, `brand`, `min_price`, `max_price`, `sort_by`, `page`, `per_page` |
| `GET` | `/api/products/{id}` | Mengambil detail 1 produk lengkap dengan spesifikasi, review, dan garansi |
| `POST` | `/api/score` | Menghitung rekomendasi terbobot berdasarkan input preferensi 4-langkah wizard |
| `POST` | `/api/compare` | Membandingkan 2-4 produk dan menentukan `best_product_id` di setiap baris spesifikasi |
| `GET` | `/api/prices/{id}` | Mengambil harga live dari Tokopedia, Shopee, dan Lazada via web scraper |
| `GET` | `/api/brands` | Mengambil daftar brand unik yang tersedia |
| `GET` | `/api/categories` | Mengambil daftar kategori produk |

---

## 🧠 Algoritma Scoring Engine (MCDA)

Mesin kalkulasi di `backend/app/scoring.py` mengimplementasikan teknik **Multi-Criteria Decision Analysis (MCDA)**:

1. **Pembobotan Preferensi Pengguna**: Menerima bobot prioritas pengguna (skala 1 - 5) untuk 6 dimensi utama:
   - *Performa*, *Kamera*, *Baterai*, *Layar*, *Build Quality*, dan *Value for Money*.
2. **Peningkatan Bobot Berdasarkan Skenario**: Skenario seperti *Gaming* otomatis menambah bobot performa (+15%) dan layar (+8%). Skenario *Fotografi* meningkatkan bobot kamera (+20%). Skenario *Pelajar* menambah bobot value (+15%).
3. **Normalisasi Vektor**: Seluruh bobot dinormalisasi sehingga total $\sum w_i = 1.0$.
4. **Perhitungan Skor Dasar**: $\text{Skor Dasar} = \sum_{i=1}^{n} (w_i \times s_i)$, di mana $s_i$ adalah skor teruji perangkat pada dimensi $i$ (skala 0 - 100).
5. **Modifikator Kepatuhan Anggaran (Budget Modifier)**:
   - Produk di dalam rentang budget: $+5.0$ poin bonus.
   - Produk di bawah budget (hemat): $+2.0$ poin bonus.
   - Produk melebihi budget $\le 20\%$: $-5.0$ poin penalti.
   - Produk melebihi budget $> 20\%$: $-15.0$ poin penalti.
6. **Pembangkit Narasi Kontekstual (*Why This Product?*)**: Mesin mengekstrak 3 dimensi kontributor tertinggi dan menyusun kalimat penjelasan dalam bahasa Indonesia alami.

---

## 🛒 Scraping Harga Marketplace Live

Modul `backend/app/scraper.py` menggunakan **Httpx Asynchronous Client** dan **BeautifulSoup4**:
* Memindai halaman hasil pencarian resmi dari **Tokopedia**, **Shopee**, dan **Lazada** secara paralel menggunakan `asyncio.gather()`.
* **Sistem Fail-Safe & Fallback**: Mengingat proteksi anti-bot Cloudflare/WAF pada marketplace produksi, modul ini dilengkapi mekanisme fallback cerdas dengan data harga realistis pasar Indonesia yang bervariasi dinamis, sehingga antarmuka pengguna tidak pernah kosong atau rusak.
* Menampilkan badge **"Harga Termurah"** otomatis pada marketplace dengan penawaran paling hemat, serta tautan langsung untuk mempermudah transaksi.

---