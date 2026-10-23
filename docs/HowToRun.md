# Panduan Menjalankan CompareBuy (How to Run) 📱⚡

Dokumen ini berisi panduan lengkap langkah demi langkah untuk menyiapkan, mengonfigurasi, menguji, dan menjalankan platform **CompareBuy** (FastAPI Backend + Next.js Frontend) pada lingkungan lokal menggunakan Windows PowerShell.

---

## 1. Prasyarat Sistem & Versi Runtime

Pastikan perangkat Anda telah terpasang perangkat lunak berikut:

| Perangkat Lunak | Versi Minimal yang Didukung | Versi Terverifikasi | Perintah Pengecekan |
|---|---|---|---|
| **Python** | 3.12+ / 3.13+ | Python 3.13.7 | `python --version` |
| **Node.js** | v18.x / v20.x+ | Node.js v20+ | `node -v` |
| **npm** | v9.x+ / v10.x+ | npm v10+ | `npm -v` |
| **PostgreSQL** *(Opsional)* | 15+ / 16+ / 18+ | PostgreSQL 18.6 | `Get-Service -Name *postgres*` |

> [!NOTE]
> **Mode Database vs Mode In-Memory Fallback & Transparansi Data:**
> CompareBuy memiliki arsitektur cerdas dan tangguh. Jika PostgreSQL tidak diinstal atau dinonaktifkan, backend FastAPI **secara otomatis beralih ke Mode In-Memory Fallback** menggunakan dataset 20 produk terkurasi di `backend/app/products.py`. Seluruh fitur scoring, perbandingan, katalog, dan wizard tetap berjalan 100% normal tanpa database.
> Data katalog mengedepankan transparansi: produk dengan SKU unverified (seperti Acer Aspire 5 Rp8.499.000) secara tegas dilabeli sebagai *Harga Acuan Katalog (Belum Terverifikasi)* untuk konfigurasi dasar RAM 8 GB / SSD 512 GB, dan tidak diasumsikan sebagai MSRP peluncuran resmi.

---

## 2. Struktur Folder Proyek

```text
Rekayasa Perangkat Lunak/
├── backend/                       # Python FastAPI Microservice
│   ├── app/                       # Logika aplikasi (models, routers, scoring, scraper, db)
│   ├── migrations/                # Alembic schema migrations (001, 002, 003)
│   ├── tests/                     # Rangkaian unit test & test_api integrasi
│   ├── .env.example               # Templat environment backend
│   ├── alembic.ini                # Konfigurasi migrasi database
│   ├── requirements.txt           # Daftar dependensi Python
│   └── seed.py                    # Seeder katalog idempotent
├── frontend/                      # Next.js App Router (React 18)
│   ├── src/                       # Komponen UI, halaman (catalog, compare, wizard), context
│   ├── .env.example               # Templat environment frontend
│   └── package.json               # Konfigurasi dependensi Node.js
└── venv/                          # Python Virtual Environment
```

---

## 3. Persiapan Variabel Lingkungan (Environment Variables)

Salin template konfigurasi resmi yang telah disediakan tanpa menyalin atau menyebarkan kredensial rahasia:

### A. Backend (`backend/.env`)
Buka terminal PowerShell di folder `backend/`:
```powershell
cd "c:\KULIAH\Semester 3\Rekayasa Perangkat Lunak\backend"
Copy-Item .env.example .env
```
Isi konfigurasi pada file `backend/.env`:
- **Jika menggunakan PostgreSQL lokal:**
  ```env
  ALLOWED_ORIGINS=http://localhost:3000
  DATABASE_URL=postgresql://USERNAME_POSTGRES:PASSWORD_POSTGRES@localhost:5432/comparebuy
  ```
  *(Ganti `USERNAME_POSTGRES` dan `PASSWORD_POSTGRES` dengan kredensial PostgreSQL lokal Anda).*
- **Jika menggunakan Mode In-Memory Fallback (Tanpa PostgreSQL):**
  Cukup kosongkan nilai `DATABASE_URL` atau jangan sertakan variabel tersebut:
  ```env
  ALLOWED_ORIGINS=http://localhost:3000
  ```

### B. Frontend (`frontend/.env.local`)
Buka terminal PowerShell di folder `frontend/`:
```powershell
cd "c:\KULIAH\Semester 3\Rekayasa Perangkat Lunak\frontend"
Copy-Item .env.example .env.local
```
Isi konfigurasi `frontend/.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 4. Konfigurasi Database PostgreSQL (Opsional)

> [!IMPORTANT]
> **Penting:** Lewati langkah ini jika Anda ingin menjalankan aplikasi dalam **Mode In-Memory Fallback** tanpa PostgreSQL. Pada mode fallback, Anda **TIDAK PERLU** menjalankan migrasi maupun seeder PostgreSQL.

Jika Anda ingin mengaktifkan persistensi PostgreSQL:

1. **Pastikan Service PostgreSQL Aktif:**
   ```powershell
   Get-Service -Name *postgres*
   ```
   Jika statusnya belum *Running*, aktifkan service via PowerShell Administrator:
   ```powershell
   Start-Service postgresql*
   ```

2. **Buat Database `comparebuy`:**
   Masuk ke command line `psql` PostgreSQL:
   ```sql
   CREATE DATABASE comparebuy;
   ```

3. **Jalankan Migrasi Skema Database (Alembic):**
   *Wajib dijalankan terlebih dahulu sebelum seeder agar struktur constraint terpasang benar:*
   ```powershell
   cd "c:\KULIAH\Semester 3\Rekayasa Perangkat Lunak\backend"
   ..\venv\Scripts\alembic.exe upgrade head
   ```
   Perintah ini akan mengeksekusi 3 migrasi:
   - `001_initial_schema` (pembuatan tabel inti)
   - `002_database_constraints` (tipe JSONB dan domain constraints)
   - `003_add_warranty_details` (kolom garansi suku cadang vs servis resmi)

4. **Eksekusi Seeder Data Katalog:**
   ```powershell
   ..\venv\Scripts\python.exe seed.py
   ```
   *Seeder ini bersifat idempotent dan aman dijalankan berulang kali tanpa membuat duplikasi data.*

---

## 5. Menjalankan Backend (FastAPI)

1. Buka PowerShell dan masuk ke direktori backend:
   ```powershell
   cd "c:\KULIAH\Semester 3\Rekayasa Perangkat Lunak\backend"
   ```

2. Jalankan Uvicorn menggunakan interpreter Python lokal (disarankan mengaktifkan UTF-8 console untuk Windows):
   ```powershell
   $env:PYTHONUTF8=1
   ..\venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **Verifikasi Backend:**
   - Akses Healthcheck: `http://localhost:8000/health` (menghasilkan status `ok`).
   - Akses Root Status: `http://localhost:8000/` (menghasilkan versi API).
   - Akses Swagger UI Interaktif: `http://localhost:8000/docs`.
   - Akses Dokumentasi ReDoc: `http://localhost:8000/redoc`.

---

## 6. Menjalankan Frontend (Next.js)

1. Buka terminal PowerShell baru dan masuk ke direktori frontend:
   ```powershell
   cd "c:\KULIAH\Semester 3\Rekayasa Perangkat Lunak\frontend"
   ```

2. Pastikan dependensi Node.js terpasang:
   ```powershell
   npm install
   ```

3. Jalankan server pengembangan Next.js:
   ```powershell
   npm run dev
   ```

4. Buka peramban (browser) dan akses aplikasi di:
   ```text
   http://localhost:3000
   ```

---

## 7. Menjalankan Rangkaian Pengujian (Testing)

Sebelum mendemonstrasikan atau menyerahkan proyek, verifikasi integritas kode dengan menjalankan pengujian aktual:

### A. Rangkaian Unit Test Backend (228 Tests)
Jalankan dari folder `backend/`:
```powershell
cd "c:\KULIAH\Semester 3\Rekayasa Perangkat Lunak\backend"
..\venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
```
*Hasil yang diharapkan: `=== ALL 228 UNIT TESTS PASSED ===`*

### B. Pengujian Integrasi API & Entity DB
Jalankan dari folder `backend/`:
```powershell
..\venv\Scripts\python.exe -m tests.test_api
```
*Hasil yang diharapkan: `=== API CORE ENDPOINTS AND AVAILABLE DATABASE CHECKS PASSED ===`*

### C. Uji Kompilasi Produksi Frontend
Jalankan dari folder `frontend/`:
```powershell
cd "c:\KULIAH\Semester 3\Rekayasa Perangkat Lunak\frontend"
npm run build
```
*Hasil yang diharapkan: `✓ Compiled successfully` dan `Generating static pages (7/7)`.*

---

## 8. Panduan Troubleshooting Kendala Umum

1. **Port 8000 atau Port 3000 Sedang Digunakan:**
   - Cari proses yang menggunakan port:
     ```powershell
     Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object OwningProcess
     ```
   - Hentikan proses tersebut jika merupakan instans lama:
     ```powershell
     Stop-Process -Id <PID> -Force
     ```

2. **Kendala Koneksi Database PostgreSQL:**
   - Jika terminal menampilkan `Could not initialize database engine: ... Falling back to in-memory mode`, backend tidak akan crash. Aplikasi tetap berfungsi normal menggunakan data memori.
   - Periksa kembali format `DATABASE_URL` di `backend/.env` dan pastikan nama database `comparebuy` telah dibuat di PostgreSQL.

3. **Kendala CORS pada Frontend:**
   - Jika konsol browser menampilkan pesan blocked by CORS policy, pastikan file `backend/.env` memuat `ALLOWED_ORIGINS=http://localhost:3000`. Restart server backend setelah memperbarui `.env`.

4. **Data Harga Marketplace Berstatus Fallback:**
   - Tokopedia, Shopee, dan Lazada menerapkan proteksi anti-bot/WAF. Apabila scraping langsung dibatasi, modul `backend/app/scraper.py` secara otomatis menggunakan data fallback acuan yang deterministik.
   - UI akan menandai penawaran dengan badge jujur: *"Data Acuan Fallback"* dan `captured_at: null`. Ini adalah perilaku sistem yang didesain tangguh (*fail-safe by design*), bukan bug.
