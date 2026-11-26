# Deskripsi aplikasi CompareBuy

Diperbarui 26 November 2026 berdasarkan source versi 1.1.0. Dokumen ini menjelaskan
implementasi; ide awal dan hasil uji historis dipisahkan di [indeks docs](README.md).

CompareBuy membantu pengguna membandingkan smartphone, laptop, tablet, TWS/audio,
dan smartwatch melalui katalog, wizard rekomendasi, serta matriks perbandingan.
Aplikasi tidak menyediakan akun pengguna, autentikasi pengguna, atau panel
administrasi produk. Katalog awal berisi 20 produk kurasi; isi database dapat berubah
setelah pengisian atau pembaruan data.

## Stack dan arsitektur

| Bagian | Implementasi |
| --- | --- |
| Frontend | Next.js 16.4.5 App Router, React/React DOM 19.2.9, JavaScript/JSX |
| Runtime frontend | Node.js 24.x, sesuai package.json dan workflow |
| Tampilan | Tailwind CSS 3, Lucide React |
| Backend | FastAPI, Pydantic 2, Python 3.12 sebagai runtime Docker |
| Database | PostgreSQL, SQLAlchemy 2.x, Alembic, seeder idempotent |
| Harga marketplace | HTTPX, BeautifulSoup4, worker scraping dan cache layanan harga |
| Deployment frontend | Vercel melalui gate GitHub Actions P11 |
| Deployment backend | Konfigurasi Render tersedia; Railway sebagai alternatif konfigurasi |

Backend membaca katalog melalui repository database. Fallback memori backend hanya
berlaku bila development/test dan `ALLOW_CATALOG_FALLBACK=true`. Default lingkungan
adalah production; pada production atau Render, database gagal mengakibatkan HTTP
503 pada API inti/readiness, bukan penggantian diam-diam dengan seed memori.

Frontend memiliki dataset cadangan tersendiri di `frontend/src/data/products.js`.
Kegagalan API dapat mengaktifkan fallback klien. Ini mempertahankan fungsi lokal,
tetapi bukan jaminan data sama mutakhirnya dengan PostgreSQL. Persistensi pilihan
komparasi dan tema memakai localStorage, bukan database.

## Fitur yang tersedia

- **Katalog**: pencarian nama, brand, deskripsi, dan tag; filter kategori, brand,
  rentang harga; sorting skor, harga, atau nama; detail produk dan dock komparasi.
  API juga mendukung filter tag serta pagination. UI katalog tidak menyediakan
  semua parameter API sebagai kontrol tersendiri.
- **Wizard empat langkah**: kategori ? anggaran ? skenario ? prioritas. UI meminta
  minimal satu skenario. Enam prioritas dapat diubah pengguna; engine menghitung
  delapan dimensi, termasuk audio/software dengan bobot default jika tidak diisi.
- **Rekomendasi**: bobot skenario dinormalisasi, skor produk dibobotkan, lalu diberi
  modifier budget (+5 dalam rentang, +2 di bawah, -5 di atas hingga 20%, -15 jika
  lebih). Hasil memuat ranking, breakdown, alasan, dan status budget. API gagal
  dapat memicu perhitungan lokal klien.
- **Komparasi**: dua sampai empat produk; urutan pilihan dipertahankan, seri dan
  dimensi yang tidak berlaku ditangani, serta kondisi kosong/satu produk tersedia.
  Pilihan disimpan di `comparebuy_dock`, divalidasi, dideduplikasi, dan dibatasi empat.
- **Detail produk**: spesifikasi, ringkasan ulasan, garansi/purna jual, marketplace
  dan value. Informasi harga dan garansi harus dibaca bersama konfigurasi varian
  serta status verifikasinya; semua SKU tidak otomatis terverifikasi.
- **Tema**: dark/light mode, tersimpan pada `comparebuy_theme`.

Skor kartu katalog berbeda dari skor personal wizard: kartu memakai rata-rata lima
dimensi dengan pembulatan. Sejak P11, nilai sah `0` dipertahankan; hanya null atau
undefined yang memakai default 50.

## Batas klaim data

Ringkasan ulasan berasal dari data yang disediakan katalog; keberadaan rating atau
pros/cons tidak membuktikan ulasan telah dikumpulkan live, diverifikasi pembelinya,
atau dihasilkan oleh layanan AI eksternal. Produk yang tidak punya data ulasan
memerlukan tampilan tanpa klaim rating/review yang dibuat-buat.

Scraping marketplace dapat dibatasi halaman dinamis atau anti-bot. Setiap penawaran
backend dibedakan melalui `source` (`scraped`/`fallback`). Fallback backend bersifat
deterministik, tanpa variasi acak, dan `captured_at` tidak mengklaim tangkapan live.
Fallback harga frontend merupakan jalur terpisah dengan metadata sendiri. Harga,
nama seller, dan ketersediaan pada data acuan tidak menjamin stok/harga aktual.
Snapshot harga database append-only dan tidak mengganti harga acuan produk secara
langsung. Jangan menyimpulkan semua penawaran atau garansi resmi telah terverifikasi.

## Endpoint utama

| Method | Path | Tujuan |
| --- | --- | --- |
| GET | `/` | Metadata layanan; bukan readiness database |
| GET | `/health` | Readiness: connected, degraded pada fallback lokal, atau HTTP 503 |
| GET | `/api/products` | Katalog, search/filter/sort, page dan per_page |
| GET | `/api/products/{product_id}` | Detail produk |
| GET | `/api/brands`, `/api/tags`, `/api/categories` | Metadata filter |
| POST | `/api/score` | Rekomendasi personal |
| POST | `/api/compare` | Komparasi dua sampai empat ID |
| GET | `/api/prices/{product_id}` | Penawaran harga dengan sumber data |

Schema Pydantic berada di `backend/app/models.py`; entitas database di
`backend/app/entities/`, akses data di `backend/app/repositories/`, dan migrasi di
`backend/migrations/`. Field garansi terstruktur mencakup parts, labor, baterai,
charger, tipe layanan, sumber, dan status verifikasi. Spesifikasi dapat memuat
`base_configuration`, `variants_note`, `ports`, serta `charging`.

## Struktur dan pengoperasian

```text
CompareBuy/
  .github/workflows/p11.yml
  backend/
    app/{routers,entities,repositories,security}/
    app/{main,db,models,products,scoring,scraper,price_service,scrape_worker}.py
    migrations/
    tests/
    seed.py
    requirements.txt
  frontend/
    src/{app,components,context,data,lib}/
    tests/
    scripts/
    package.json
    eslint.config.mjs
    vercel.json
  scripts/p11/
  docs/{qa,p11}/
```

Ikuti [HowToRun.md](HowToRun.md) untuk environment, PostgreSQL, fallback lokal,
frontend, dan perintah test. CI P11 memisahkan minimal 200 unit test frontend dari
integrasi backend dan smoke deployment. Hasil backend bergantung database test;
SKIP tidak dihitung passed.

Bukti rilis 1.1.0, issue, screenshot, serta alur merah/hijau ada pada
[laporan P11](p11/README.md) dan [GitHub Release](https://github.com/FirmanFelixNduru/RPLWeb/releases/tag/v1.1.0).
URL produksi yang dicatat pada rilis: https://comparebuy-livid.vercel.app dengan
backend https://comparebuy-api.onrender.com. Status live tidak diuji ulang sebagai
bagian pembaruan teks ini.
