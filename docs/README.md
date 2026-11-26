# Indeks dokumentasi CompareBuy

Ditinjau 26 November 2026 berdasarkan source versi 1.1.0. Pembaruan ini memeriksa
kesesuaian teks dengan kode dan artefak yang tersimpan, bukan pengujian ulang
layanan produksi atau seluruh suite. Angka passed pada laporan selalu merujuk
commit dan waktu pengujiannya.

## Panduan implementasi dan operasional

| Dokumen | Gunakan untuk |
| --- | --- |
| [HowToRun](HowToRun.md) | Runtime, setup lokal, database, fallback, test, dan deployment |
| [Deskripsi aplikasi](deskripsi-aplikasi.md) | Fitur yang diimplementasikan, stack, API, dan batas klaim data |
| [P11](p11/README.md) | Branch rilis, 200 unit test, gate CI/CD, screenshot, dan hasil merah/hijau |
| [Release 1.1.0](https://github.com/FirmanFelixNduru/RPLWeb/releases/tag/v1.1.0) | Paket bukti produksi final dan screenshot rilis |

Versi dependency mengacu pada [package.json](../frontend/package.json) dan
[requirements.txt](../backend/requirements.txt). Perilaku fallback backend
mengacu pada [db.py](../backend/app/db.py); otomatisasi pada
[workflow P11](../.github/workflows/p11.yml). Bila konfigurasi atau kode berubah,
periksa sumber tersebut sebelum memakai instruksi lama.

## Laporan dan arsip

| Dokumen | Status dan batas penggunaan |
| --- | --- |
| [QA deployment](qa/README.md) | Bukti historis 10 bug #5–#14 dan 105 test pada tahap QA sebelum P11 |
| [Checklist MVP](checklist_mvp.md) | Checklist historis, ditambah ringkasan perubahan P11; angka/backend/video lama tidak diuji ulang |
| [MVP Pertemuan 5](MVP-v1.md) | Laporan tahap awal; contoh output dan endpoint lama dipertahankan sebagai arsip |
| [Requirement web](requirement-web.md) | Spesifikasi rancangan awal, dengan konteks database/stack yang diperbarui; bukan bukti seluruh persyaratan selesai |
| [Permintaan perbaikan](perbaikan.md) | Daftar revisi UI terdahulu, bukan backlog aktif |
| [Prompt revisi](revisi.md) | Riwayat instruksi tahap revisi, bukan prosedur kerja terkini |
| [Pemaparan tema](pemaparan.md) | Proposal beberapa tema; klaim aspiratif bukan hasil verifikasi aplikasi |
| [Output ide](output-ide.md) | Alternatif CompareBuy/Lapor Fasilitas/KosKu; bukan tiga modul aplikasi |
| [Contoh format](format-jawaban.md) | Prompt proyek Lecturer GitHub Tracker; tidak menggambarkan stack CompareBuy |
| [Video demo](demo.mp4) | Rekaman terdahulu; bukan bukti tampilan atau deployment saat ini |

JSON, TAP, JUnit, screenshot, dan video disimpan sebagai bukti historis asli.
Hasil failed pada tahap merah P11 sengaja dipertahankan: hasil tersebut membuktikan
gate memblokir build/deploy, bukan menunjukkan bahwa rilis akhirnya masih gagal.

## Koreksi utama pada peninjauan ini

- Runtime frontend adalah Node.js 24.x, Next.js 16.4.5, React 19.2.9; bukan Node
  18/20, Next.js 14, atau React 18 yang tertulis pada panduan lama.
- PostgreSQL, repository SQLAlchemy, dan migrasi Alembic sudah diimplementasikan.
  Fallback katalog backend tidak otomatis aktif; production fail closed.
- Lint sudah dikonfigurasi. Gate P11 mencatat minimal 200 unit test frontend;
  hasil backend yang skipped tidak boleh dihitung passed.
- Frontend menggunakan pipeline Actions. Backend Render dikelola terpisah.
- Rating, garansi, dan harga harus dibaca bersama sumber/status verifikasi;
  tidak ada jaminan semua ulasan terverifikasi atau semua harga live.
