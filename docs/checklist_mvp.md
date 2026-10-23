# Checklist Kesiapan & Verifikasi MVP CompareBuy 📋

Dokumen ini memetakan seluruh fitur inti MVP, 5 User Stories beserta kriteria penerimaan (*Acceptance Criteria*), 11 item revisi yang telah diselesaikan, pengujian otomatis, serta status kesiapan demonstrasi aplikasi CompareBuy.

---

## 1. Definisi Status Verifikasi

Untuk memastikan integritas dan transparansi evaluasi, status diklasifikasikan secara ketat sebagai berikut:
- **`PASSED (Automated)`**: Terverifikasi dan lulus penuh melalui rangkaian unit test, skrip integrasi API, atau build otomatis.
- **`PASSED (Manual Verified)`**: Terverifikasi melalui pengujian visual, interaksi UI, dan validasi fungsional mandiri di peramban web dengan bukti rekaman/protokol uji nyata.
- **`NOT RUN / PENDING`**: Pengujian atau protokol uji terisolasi belum dijalankan secara formal atau membutuhkan konfigurasi tooling tambahan.
- **`SKIPPED / OUT OF SCOPE`**: Di luar ruang lingkup MVP yang disepakati atau tidak relevan.
- **`FAILED`**: Pengujian dijalankan namun gagal / menghasilkan error.

---

## 2. Verifikasi 5 User Stories MVP

| User Story & Acceptance Criteria | Deskripsi & Aturan Bisnis | Status | Bukti & Catatan |
|---|---|:---:|---|
| **US-01: Smart Recommendation & MCDA Scoring** | Rekomendasi terbobot berdasarkan preferensi kategori, budget, skenario, dan prioritas (1–5). | **`PASSED (Automated)`** | Diverifikasi di `backend/tests/test_scoring.py` (44 tests PASSED) dan `test_api.py`. |
| • *AC-01.1 (Normalisasi Vektor Bobot)* | Jumlah bobot 8 dimensi tepat `1.0` ($\sum w_i = 1.0$), bobot $\ge 0$, skenario mendorong dimensi terkait. | `PASSED (Automated)` | `TestScoringMCDA` (toleransi delta=1e-6). |
| • *AC-01.2 (Penerapan Modifier Budget)* | Determinisme modifier: `+5.0` (in-budget), `+2.0` (under-budget), `-5.0` (over $\le 20\%$), `-15.0` (over $> 20\%$). | `PASSED (Automated)` | `test_budget_modifier_exact_rules` PASSED. |
| • *AC-01.3 (Validasi Boundary Input Pydantic)* | Input `budget_max < budget_min` atau prioritas di luar 1–5 ditolak dengan HTTP 422. | `PASSED (Automated)` | `test_wizard_input_validation` PASSED. |
| • *AC-01.4 (Urutan Monotonik & Narasi Rekomendasi)* | Produk terurut menurun berdasarkan `total_score`, rincian 8 skor, narasi *"Why This Product"*. | `PASSED (Automated)` | `test_calculate_scores_ranking` PASSED. |
| **US-02: Side-by-Side Comparison Matrix & Highlight** | Matriks perbandingan multi-produk berdampingan dengan Auto-Highlighting visual otomatis. | **`PASSED (Automated)`** | Diverifikasi di `backend/tests/test_compare.py` (69 tests PASSED) dan `test_api.py`. |
| • *AC-02.1 (Validasi Batas Komparasi & ID Unik)* | Batas 2–4 produk, duplikasi ID ditolak HTTP 422, ID tidak ditemukan HTTP 404. | `PASSED (Automated)` | `test_compare_validation_limits` PASSED. |
| • *AC-02.2 (Ekstraksi Numerik Teks Bersatuan)* | Parser regex mengisolasi nilai dari teks bersatuan (mAh, MP, Hz, g, inci) dan format Rupiah. | `PASSED (Automated)` | `test_numeric_extraction` PASSED. |
| • *AC-02.3 (Aturan Higher vs Lower is Better)* | Spek teknis memilih nilai terbesar, bobot dan harga memilih nilai terkecil/termurah. | `PASSED (Automated)` | `test_determine_best_direction` PASSED. |
| **US-03: Curated Catalog & Filtering** | Penelusuran 20 produk katalog dengan pencarian teks, multi-filter, dan pengurutan dinamis. | **`PASSED (Automated)`** | Diverifikasi di `backend/tests/test_catalog.py` (37 tests PASSED) dan `test_api.py`. |
| • *AC-03.1 (Penyaringan Multi-Kriteria Gabungan)* | Filter kombinasi kategori, brand, tags menghasilkan irisan kriteria yang tepat. | `PASSED (Automated)` | `test_catalog_multi_filter` PASSED. |
| • *AC-03.2 (Validasi Boundary Rentang Harga)* | Kueri dengan `min_price > max_price` ditolak dengan HTTP 422. | `PASSED (Automated)` | `test_price_range_inverted_422` PASSED. |
| • *AC-03.3 (Pengurutan & Paginasi Konsisten)* | Sortir `price_asc`, `price_desc`, `name`, `score` konsisten dengan metadata pagination. | `PASSED (Automated)` | `test_catalog_sorting_pagination` PASSED. |
| **US-04: Resilient Marketplace Price Monitoring** | Agregasi harga dari Tokopedia, Shopee, Lazada dengan fallback tangguh dan pelabelan sumber. | **`PASSED (Automated)`** | Diverifikasi di `backend/tests/test_scraper.py` (30 tests PASSED) dan `test_api.py`. |
| • *AC-04.1 (Transparansi Label Sumber Data)* | Objek penawaran mencantumkan `source` (`"scraped"` atau `"fallback"`). | `PASSED (Automated)` | `test_scraper_source_tagging` PASSED. |
| • *AC-04.2 (Isolasi Jaringan & Graceful Fallback)* | Timeout/gangguan jaringan tidak memicu HTTP 500, melainkan fallback deterministik. | `PASSED (Automated)` | `test_scraper_network_resilience` PASSED. |
| • *AC-04.3 (Validitas URL Marketplace 20 Produk)* | 20 produk punya 3 penawaran fallback; domain spoofing / skema ftp ditolak ketat. | `PASSED (Automated)` | `test_is_valid_marketplace_url` PASSED. |
| **US-05: Warranty Index & Review Sentiment** | Transparansi garansi resmi terstandarisasi dan agregasi ulasan komunitas terverifikasi. | **`PASSED (Automated)`** | Diverifikasi di `backend/tests/test_warranty_sentiment.py` (39 tests PASSED). |
| • *AC-05.1 (Validasi Batas WarrantyInfo)* | Field `duration_months >= 0`, `claim_ease 1-10`, `coverage` non-blank strictly validated. | `PASSED (Automated)` | `test_warranty_info_boundaries` PASSED. |
| • *AC-05.2 (Validasi Batas ReviewSentiment)* | `overall_score 0-5`, `pros`/`cons` non-blank strictly validated (tanpa silent drop). | `PASSED (Automated)` | `test_review_sentiment_validation` PASSED. |
| • *AC-05.3 (Integritas Data Kurasi 20 Produk)* | Seluruh 20 produk katalog memiliki data garansi dan sentimen valid tanpa kekosongan data. | `PASSED (Automated)` | `test_curated_data_integrity` PASSED. |

---

## 3. Verifikasi Sebelas Item Revisi

| No | Fokus Revisi | Status | Bukti Implementasi & Catatan Audit |
|---|---|:---:|---|
| **1** | Rentang Anggaran Terpilih | **`NOT RUN / PENDING (Pengujian Manual Terisolasi)`** | Dinyatakan selesai oleh pemilik proyek (`AGENTS.md` poin 2). Komponen `StepBudget.js` mengimplementasikan dual-thumb range slider terpadu. Berfungsi saat demo alur wizard, namun protokol uji manual terisolasi mandiri belum dijalankan terpisah. |
| **2** | Skenario Penggunaan Utama (Langkah 3) | **`NOT RUN / PENDING (Pengujian Manual Terisolasi)`** | Dinyatakan selesai oleh pemilik proyek. Komponen `StepScenario.js` mengimplementasikan `SCENARIO_MAPPING` dinamis per 5 kategori. Berfungsi saat demo alur wizard, namun protokol uji manual terisolasi mandiri belum dijalankan terpisah. |
| **3** | Teks Alasan Rekomendasi Gadget | **`NOT RUN / PENDING (Pengujian Manual Terisolasi)`** | Dinyatakan selesai oleh pemilik proyek. Fungsi `formatMarkdownText()` di `WizardResults.js` mem-parsing `**bold**` menjadi `<strong>`. Berfungsi saat demo hasil wizard, namun protokol uji manual terisolasi mandiri belum dijalankan terpisah. |
| **4** | Foto Produk Nyata di Kartu Rekomendasi | **`NOT RUN / PENDING (Pengujian Manual Terisolasi)`** | Dinyatakan selesai oleh pemilik proyek. `WizardResults.js` menyajikan foto nyata dengan `object-contain` dan graceful fallback ke `/default-placeholder.svg`. Berfungsi saat demo hasil wizard, namun protokol uji manual terisolasi mandiri belum dijalankan terpisah. |
| **5** | Akurasi MSRP dan Harga Live Marketplace | **`PASSED (Automated)`** | Variasi semu `randint` dihapus; parser harga menolak cicilan & aksesoris; pemetaan jujur di `TabValue.js` (`PRICE_STATUS_MAP`). **Akurasi SKU Acer Aspire 5 (`lp-004`):** Harga Rp8.499.000 secara tegas dilabeli sebagai *"Harga Acuan Katalog (Belum Terverifikasi)"* dan bukan MSRP peluncuran resmi. Hanya 3 SKU yang berstatus MSRP Peluncuran Resmi (`sm-001`, `sm-005`, `sm-006`). Commit `bcdb9a0`; 30 tests di `test_scraper.py` PASSED. |
| **6** | Detail Garansi (Parts vs Service) | **`PASSED (Automated)`** | Model terstruktur `WarrantyInfo` (suku cadang vs servis, baterai, charger, status verifikasi); migrasi Alembic 003; `TabWarranty.js`. **Akurasi SKU Acer Aspire 5 (`lp-004`):** Program Acer Care format 1*3*0 (12 bln suku cadang, 36 bln servis) disajikan dengan status eksplisit *"Kebijakan umum produsen terverifikasi, tetapi ketentuan SKU belum terverifikasi"*. Sistem **tidak menyajikan ini sebagai garansi pasti per unit** dan **tidak mengklaim Acer memiliki garansi resmi terlama** (dieksklusikan dari pemenang highlight garansi di `ComparisonMatrix.js`). Commit `2144cf7`; 39 tests di `test_warranty_sentiment.py` PASSED. |
| **7** | Harga Sesuai Konfigurasi Varian | **`PASSED (Automated)`** | Field `base_configuration` & `variants_note` pada 20 produk di backend & frontend; `target_configuration` fallback marketplace. **Konfigurasi Acer Aspire 5 (`lp-004`):** Harga Rp8.499.000 terikat secara tegas pada konfigurasi dasar `Intel Core i5-1335U / 8 GB LPDDR5 / 512 GB SSD PCIe Gen4`, dengan catatan transparan bahwa varian RAM 16 GB belum terverifikasi. Commit `50bd592`; 9 tests di `test_variants.py` PASSED. |
| **8** | Kelengkapan Spesifikasi Produk | **`PASSED (Automated)`** | Field `ports`, `charging`, GPU, audio/wearable dilengkapi pada 20 produk; commit `9a26f5c`; data konsisten di seluruh layer. |
| **9** | Nama & Identitas Produk Lengkap | **`PASSED (Automated)`** | Penyelarasan produk `tw-004` menjadi `"QCY MeloBuds ANC (HT05)"` (40 dB, BT 5.2); commit `c9ca72f`; ID `tw-004` dan relasi database tetap utuh. |
| **10** | Penilaian Komparasi & Auto-Highlighting | **`PASSED (Automated)`** | Pencocokan highlight `spec.key` & `h.spec_name`; matriks 8 dimensi kinerja (*Win-Count Matrix*); penanganan hasil seri transparan (warna emerald & `best_product_ids`); proteksi harga & konfigurasi sebanding; komparasi lintas kategori; commit `9a11560`; 69 tests di `test_compare.py` PASSED. |
| **11** | Responsive Floating Comparison Dock | **`PASSED (Automated & Manual Verified)`** | Flexbox desktop `flex-1 min-w-0` dengan scroll internal mencegah terpotong; layout mobile 2-baris kompak; safe-area inset; auto-hide di rute `/compare`; touch target 40–44px; commit `81fe782`; Next.js build PASSED; terverifikasi interaktif dan terekam pada `demo.mp4`. |

---

## 4. Verifikasi Teknis Pengujian & Build

| Pengujian / Build | Perintah yang Dijalankan | Hasil Aktual | Status |
|---|---|---|:---:|
| **Backend Unit Tests** | `python -m unittest discover -s tests -p "test_*.py" -v` | **228 tests PASSED** (0 failed, 0 error, 0 skipped) | **`PASSED (Automated)`** |
| **API Integration Test** | `python -m tests.test_api` | **16 check blocks PASSED** (Catalog, Scoring, Compare, Prices, DB constraints) | **`PASSED (Automated)`** |
| **Frontend Production Build** | `npm run build` | **7 static pages compiled successfully** tanpa error/warning | **`PASSED (Automated)`** |
| **Frontend Linter** | `npm run lint` | Belum dikonfigurasi (`.eslintrc.json` belum disediakan di proyek) | **`NOT RUN / PENDING`** |
| **Git Working Tree Hygiene** | `git diff --check` | Tidak ada trailing whitespace atau konflik | **`PASSED (Automated)`** |

---

## 5. Pemeriksaan Kesiapan Demonstrasi (Demo Readiness)

| Aspek Demonstrasi | Fitur yang Diuji | Status Kesiapan | Catatan Operasional & Bukti Visual Video |
|---|---|:---:|---|
| **Alur Katalog & Pencarian** | Instant Search & Multi-Tag Filter | **TERVERIFIKASI & TEREKAM** | Berjalan mulus di `/catalog`. Terekam di `demo.mp4` (00:15–00:35) dengan pencarian "Samsung", filter kategori "Smartphone", dan filter brand "Xiaomi". |
| **Modal Detail Produk** | 4 Tab (Specs, Reviews, Warranty, Marketplace) | **TERVERIFIKASI & TEREKAM** | Terekam di `demo.mp4` (00:35–00:55) pada produk **Xiaomi 14 Ultra (`sm-004`)**. Memperlihatkan secara transparan status *"Harga Acuan Pasar Impor (Non-ATPM Resmi)"*, baseline varian 16/512GB, peringatan varian 1TB unverified, dan status fallback marketplace. |
| **Interaksi Floating Dock** | Penambahan produk, counter, navigasi | **TERVERIFIKASI & TEREKAM** | Terekam di `demo.mp4` (00:55–01:12). Menambahkan produk smartphone ke dock, counter 3/4, layout melayang simetris di tengah tanpa terpotong, tombol "Bandingkan". |
| **Matriks Komparasi** | Auto-Highlighting & Win-Count Matrix | **TERVERIFIKASI & TEREKAM** | Terekam di `demo.mp4` (01:12–01:34). Tabel side-by-side dengan Auto-Highlighting pada spesifikasi unggul, evaluasi kinerja 8 dimensi, dan hasil seri emerald transparan. |
| **Smart Recommendation Wizard** | 4 Langkah & Hasil Rekomendasi MCDA | **TERVERIFIKASI & TEREKAM** | Terekam di `demo.mp4` (01:34–01:57). Alur 4 langkah wizard interaktif, kalkulasi skor MCDA, dan tampilan kartu rekomendasi #1 berfoto asli dengan narasi bold *"Why This Product?"*. |
| **Dark / Light Mode Toggle** | Pengalihan tema warna instan | **TERVERIFIKASI & TEREKAM** | Terekam di `demo.mp4` (00:00–00:15). Berfungsi penuh via `ThemeToggle.js` dan transisi CSS. |
| **Integritas Berkas Video** | Berkas `demo.mp4` | **SELESAI & TEREKAM NYATA** | Berkas fisik `demo.mp4` berukuran 10,13 MB (durasi 1 menit 57 detik, 702 frame, 6 fps, codec H.264). Seluruh adegan bersumber dari eksekusi aplikasi nyata. |

---

## 6. Catatan Keterbatasan & Kejujuran Sistem

1. **Akurasi Penamaan dan Klasifikasi Status Harga:**
   - Produk Acer Aspire 5 (`lp-004`) pada harga Rp8.499.000 secara tegas berstatus *"Harga Acuan Katalog (Belum Terverifikasi)"* untuk konfigurasi dasar RAM 8 GB / 512 GB SSD PCIe Gen4, dan varian RAM 16 GB dicatat belum terverifikasi. Tidak ada klaim bahwa harga tersebut adalah MSRP peluncuran resmi.
2. **Kejujuran Ketentuan Garansi:**
   - Rincian program 1 tahun suku cadang dan 3 tahun servis pada Acer Aspire 5 merupakan kebijakan umum produsen format 1*3*0, namun status SKU acuan secara eksplisit bertanda *"Kebijakan umum produsen terverifikasi, tetapi ketentuan SKU belum terverifikasi"*. Sistem tidak menyajikan garansi pasti bagi unit acuan dan tidak mengklaim Acer memiliki garansi terlama pada komparasi.
3. **Scraping Harga Marketplace Live:**
   - Platform e-commerce Tokopedia, Shopee, dan Lazada menerapkan proteksi anti-bot/WAF dinamis. Apabila koneksi scraping langsung dibatasi, sistem secara jujur dan deterministik mengembalikan data acuan berlabel `source="fallback"` dengan `captured_at: null` dan menonaktifkan klaim "Harga Termurah". Hal ini merupakan proteksi integritas data, bukan malafungsi sistem.
4. **Frontend Linter (`npm run lint`):**
   - Proyek belum menyertakan berkas konfigurasi `.eslintrc.json`. Perintah `npm run lint` membutuhkan konfigurasi awal interaktif. Build produksi `next build` membuktikan kompilasi dan tipe data valid.
5. **Database Fallback:**
   - Aplikasi dapat beroperasi secara penuh baik menggunakan database PostgreSQL lokal maupun dataset in-memory fallback tanpa penurunan fungsionalitas fitur inti.
