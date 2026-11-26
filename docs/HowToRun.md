# Menjalankan dan menguji CompareBuy

Diperbarui 26 November 2026 berdasarkan kode versi 1.1.0. Perintah PowerShell
berikut dimulai dari root repository `CompareBuy`, bukan path komputer tertentu.
Hasil pengujian P11 adalah bukti historis; panduan ini tidak menyatakan deployment
atau seluruh pengujian telah diperiksa ulang pada tanggal pembaruan dokumentasi.

## Prasyarat

- Node.js **24.x**, sesuai `frontend/package.json` dan workflow P11; npm bawaan Node.
- Python **3.12** sebagai acuan runtime Docker backend; gunakan virtual environment.
- PostgreSQL untuk penggunaan database dan pengujian integrasi PostgreSQL.
- Git; GitHub CLI hanya diperlukan untuk memeriksa workflow/release.

Periksa runtime dengan `node --version`, `npm --version`, dan `python --version`.
Database produksi sudah diimplementasikan melalui SQLAlchemy dan Alembic.

## Backend lokal dengan PostgreSQL

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Jangan menimpa `.env` yang sudah berisi konfigurasi. Buat database lokal
`comparebuy` melalui PostgreSQL, lalu isi `backend/.env`:

```env
APP_ENV=development
ALLOW_CATALOG_FALLBACK=false
ALLOWED_ORIGINS=http://localhost:3000
DATABASE_URL=postgresql://USER:PASSWORD@localhost:5432/comparebuy
```

Ganti kredensial dengan milik database lokal, kemudian dari folder `backend`:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe seed.py
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Seeder mengisi katalog awal secara idempotent. Migrasi ada di `backend/migrations/`.
Gunakan URL PostgreSQL lokal, bukan database produksi, untuk setup pengembangan.

- Dokumentasi API: http://localhost:8000/docs dan http://localhost:8000/redoc.
- `GET /health`: HTTP 200 dengan `database=connected` saat database tersedia.
- Tanpa database dan tanpa izin fallback, readiness mengembalikan HTTP 503.
  Root `/` berisi metadata layanan dan bukan pengganti pemeriksaan readiness.

## Backend lokal tanpa PostgreSQL

Fallback katalog backend hanya diizinkan secara eksplisit untuk development/test.
Untuk demo lokal tanpa persistensi, gunakan konfigurasi berikut:

```env
APP_ENV=development
ALLOW_CATALOG_FALLBACK=true
DATABASE_URL=
ALLOWED_ORIGINS=http://localhost:3000
```

Lewati migrasi dan seed pada mode ini. Health check menjadi HTTP 200 dengan
`status=degraded`, `database=disconnected`, dan `fallback=enabled`.
Di produksi fallback katalog backend dilarang, termasuk saat `RENDER=true`.
Mengosongkan `DATABASE_URL` saja tidak otomatis mengaktifkan fallback. Database
produksi yang gagal tidak boleh diam-diam diganti dataset memori.

Fallback katalog **frontend** berbeda: klien dapat menampilkan dataset lokal
ketika API gagal, dengan pemberitahuan sumber data. Fallback harga marketplace
juga berbeda: penawaran acuan bukan bukti harga/ketersediaan live.

## Frontend lokal

Buka terminal kedua dari root repository:

```powershell
cd frontend
Copy-Item .env.example .env.local
npm ci --no-audit --no-fund
npm run dev
```

Isi `frontend/.env.local` dengan `NEXT_PUBLIC_API_URL=http://localhost:8000`.
Buka http://localhost:3000. Jika memakai `127.0.0.1` sebagai origin browser,
tambahkan origin yang sama ke `ALLOWED_ORIGINS`; origin ini berbeda dari localhost.
Perubahan variabel `NEXT_PUBLIC_*` memerlukan restart dev server atau build ulang.

## Unit test dan build frontend

Dari root repository:

```powershell
npm run test:ci --prefix frontend
npm run lint --prefix frontend
npm run build --prefix frontend
```

Gate P11 mensyaratkan minimal 200 test, semuanya passed, tanpa failed, skipped,
cancelled, atau todo. Hasil disimpan di `frontend/reports/` sebagai JSON, TAP,
dan JUnit. `npm test --prefix frontend` menjalankan suite tanpa gate jumlah P11.
Jumlah halaman build dan jumlah test mengikuti hasil eksekusi, bukan angka lama
yang ditulis tetap. Lint sudah memakai `frontend/eslint.config.mjs`.

## Pengujian backend

Gunakan terminal khusus pengujian dari folder `backend`. `tests/__init__.py`
memasang guard untuk mencegah pemakaian database development/production.
Untuk tes tanpa database:

```powershell
$env:DATABASE_URL=''
$env:TEST_DATABASE_URL=''
$env:APP_ENV='test'
$env:ALLOW_CATALOG_FALLBACK='true'
.\.venv\Scripts\python.exe -m unittest discover -s tests -p 'test_*.py' -v
```

Modul integrasi yang membutuhkan PostgreSQL dapat **SKIP**; laporkan jumlah
skipped terpisah, jangan menyebut semuanya passed. Tidak ada jaminan jumlah
backend tetap 228 seperti laporan MVP lama.

Untuk integrasi, buat database PostgreSQL khusus, misalnya `comparebuy_test`,
berbeda dari database development/production. Contoh pada terminal test:

```powershell
$env:TEST_DATABASE_URL='postgresql://USER:PASSWORD@localhost:5432/comparebuy_test'
$env:DATABASE_URL=$env:TEST_DATABASE_URL
$env:APP_ENV='test'
$env:ALLOW_CATALOG_FALLBACK='true'
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe seed.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -p 'test_*.py' -v
.\.venv\Scripts\python.exe -m tests.test_api
```

Migrasi dan seed di atas menulis **hanya ke database test yang ditentukan**.
`tests.test_catalog` menggunakan fixture transaksi rollback dan memerlukan
`TEST_DATABASE_URL`; baca prasyarat modul tersebut. Skrip smoke API berada di
`backend/tests/test_api.py`, bukan `backend/test_api.py`.

## Deployment dan diagnosis

Frontend P11 memakai [workflow GitHub Actions](../.github/workflows/p11.yml):
unit test/lint ? build ? deploy prebuilt ? smoke commit/route/bundle.
`frontend/vercel.json` menonaktifkan deployment langsung dari push Git.
Push `v1.0_dev` menghasilkan preview; `V1.1`/`main` menghasilkan produksi.
Konfigurasi secret, variable publik API, bukti gagal/hijau, dan rotasi token ada
pada [laporan P11](p11/README.md). Backend Render dikelola terpisah; workflow
tersebut tidak men-deploy backend.

- Database gagal: periksa koneksi, migrasi, dan readiness `/health`; produksi
  mengembalikan 503 alih-alih fallback katalog backend.
- CORS: pastikan origin frontend tepat ada di `ALLOWED_ORIGINS`; restart backend.
  Preview Vercel belum tentu termasuk origin yang diizinkan.
- Katalog fallback frontend: periksa request API, URL publik saat build, respons
  HTTP, serta CORS. Fallback bukan bukti integrasi backend berhasil.
- Harga fallback: periksa `source`; respons backend fallback tidak memakai
  timestamp tangkapan live. Bentuk metadata fallback frontend dapat berbeda.
- Port terpakai: periksa proses milik server proyek dan hentikan hanya instance
  yang memang Anda jalankan; jangan menghentikan proses lain tanpa identifikasi.

Lihat [indeks dokumentasi](README.md), [deskripsi aplikasi](deskripsi-aplikasi.md),
[hasil QA terdahulu](qa/README.md), dan [bukti rilis P11](p11/README.md).
