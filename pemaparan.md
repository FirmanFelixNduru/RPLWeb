# Pemaparan Ide Proyek RPL

---

## TEMA 1: CompareBuy — Platform Cerdas Perbandingan & Rekomendasi Perangkat Teknologi

### 1. Masalah Nyata yang Akan Diselesaikan

Konsumen yang ingin membeli perangkat teknologi (laptop, smartphone, monitor, headphone, keyboard) dihadapkan pada banjir pilihan produk yang membingungkan. Informasi tersebar di berbagai platform: marketplace, forum, media sosial, dan video review berbayar yang tidak netral. Akibatnya, calon pembeli mengalami *analysis paralysis* — menghabiskan waktu berhari-hari riset namun tetap tidak yakin dengan keputusannya.

Permasalahan ini diperparah oleh beberapa faktor: ulasan di marketplace banyak yang palsu atau disponsori, tabel spesifikasi konvensional tidak menjelaskan relevansinya terhadap kebutuhan nyata pengguna, dan hampir tidak ada platform yang membahas aspek garansi & purna jual secara transparan. Konsumen pun seringkali berakhir salah beli — membayar lebih untuk fitur yang tidak dibutuhkan, atau membeli produk murah berisiko tinggi yang bermasalah dalam jangka panjang.

### 2. Profil Target Pengguna

**Mahasiswa & Pelajar:** Memiliki anggaran terbatas dan membutuhkan perangkat yang paling sesuai kebutuhan akademik (coding, desain, gaming ringan). Mereka butuh rekomendasi yang jelas dan dapat dipertanggungjawabkan secara logis, bukan sekadar "kata orang".

**Pekerja & Profesional:** Membutuhkan perangkat kerja yang andal dengan jaminan purna jual yang baik. Mereka tidak punya waktu banyak untuk riset mendalam, sehingga butuh ringkasan perbandingan yang cepat dan terpercaya.

**Konsumen Umum:** Siapa saja yang ingin membeli gadget namun tidak memiliki latar belakang teknis. Mereka butuh penjelasan dalam bahasa yang mudah dipahami, bukan jargon spesifikasi yang membingungkan.

### 3. Manfaat Aplikasi

- Memangkas waktu riset dari berhari-hari menjadi beberapa menit melalui panduan rekomendasi interaktif (*Smart Wizard*)
- Mencegah konsumen salah beli dengan sistem skor multi-kriteria yang transparan dan dapat dijelaskan (*Explainable Recommendation*)
- Menyajikan ulasan nyata dari komunitas terverifikasi, bebas dari bias sponsor atau bot
- Memberikan informasi garansi & purna jual yang sering diabaikan platform lain, sehingga konsumen tahu risiko sebelum membeli
- Menyediakan satu pusat informasi lengkap (*one-stop hub*) — spesifikasi, harga, ulasan, dan garansi — dalam satu tempat tanpa perlu buka banyak tab
- Membantu konsumen menemukan produk paling *worth it* sesuai anggaran, bukan sekadar yang paling mahal atau paling terkenal

### 4. Daftar Fitur Inti

- **Smart Recommendation Wizard** — Panduan 4 langkah interaktif: pilih kategori, atur budget, tentukan skenario penggunaan (coding, gaming, editing, dll), dan atur prioritas trade-off
- **Weighted Dynamic Scoring Engine** — Mesin kalkulasi otomatis yang memberikan bobot penilaian secara dinamis sesuai preferensi personal pengguna
- **Side-by-Side Comparison Matrix** — Matriks perbandingan multi-produk berdampingan dengan *auto-highlighting* penanda nilai terbaik di setiap parameter
- **Floating Comparison Dock** — Dock melayang untuk mengumpulkan produk dari katalog dan membandingkannya sekaligus secara instan
- **Real User Sentiment Aggregator** — Ringkasan kelebihan & kekurangan asli dari ulasan pembeli terverifikasi berbagai platform (Reddit, RTINGS, Tokopedia Verified, Jagat Review)
- **After-Sales & Warranty Index** — Penilaian transparansi garansi (resmi vs distributor), durasi perlindungan, dan skor kemudahan klaim
- **Curated Product Catalog** — Katalog produk terkurasi dengan pencarian instan, filter multi-tag, dan pengurutan dinamis
- **Modal Rincian Produk Multi-Tab** — Detail produk dengan 4 tab: Spesifikasi, User Experience & Review, Garansi & Purna Jual, dan Value Breakdown
- **Dark Mode / Light Mode** — Dukungan tema gelap dan terang dengan transisi halus dan preferensi tersimpan

### 5. Fitur yang Tidak Dikerjakan

- Integrasi API harga langsung (*live price*) dari marketplace (Tokopedia, Shopee, Lazada)
- Sistem komentar & diskusi komunitas antar pengguna terdaftar
- Ekspor laporan perbandingan ke format PDF atau PNG
- Penambahan kategori komponen PC rakitan (GPU, CPU, Motherboard)
- Sistem wishlist & notifikasi penurunan harga
- Perbandingan harga lintas seller/toko
- Fitur autentikasi pengguna / akun pribadi

### 6. Kriteria Aplikasi Dinyatakan Berhasil

- Wizard rekomendasi berjalan lengkap dari input preferensi → proses scoring → tampil hasil rekomendasi berperingkat tanpa error
- Matriks perbandingan menampilkan data produk yang akurat dengan *auto-highlighting* nilai terbaik di setiap kolom
- Sistem scoring menghasilkan skor yang berbeda dan logis sesuai perubahan prioritas/preferensi pengguna
- Penjelasan rekomendasi (*"Why This Product?"*) tampil dengan narasi kontekstual yang relevan terhadap input pengguna
- Aplikasi dapat diakses melalui browser modern tanpa instalasi apapun (static web app)
- Dark mode dan light mode berfungsi dengan transisi halus dan preferensi tersimpan

---

## TEMA 2: KOSKU — Sistem Manajemen Kos Berbasis Web

### 1. Masalah Nyata yang Akan Diselesaikan

Pengelola kos saat ini masih mengandalkan WhatsApp sebagai satu-satunya alat komunikasi dan administrasi. Laporan kerusakan dikirim via chat yang mudah tenggelam, pengumuman penting tidak terbaca oleh semua penghuni, bukti pembayaran tersebar di berbagai percakapan, dan data penghuni tidak terkelola secara sistematis. Di sisi penghuni, mereka kesulitan memantau status tagihan, tidak tahu apakah laporan kerusakan mereka sudah ditindaklanjuti, dan informasi penting dari pemilik kos sering terlewat.

Kondisi ini menyebabkan miskomunikasi, penanganan kerusakan yang lambat, dan pengelolaan keuangan yang tidak rapi — baik dari sisi pemilik maupun penghuni kos.

### 2. Profil Target Pengguna

**Pemilik/Pengelola Kos:** Pemilik kos atau petugas yang bertanggung jawab mengelola hunian. Mereka membutuhkan satu platform terpusat untuk mendata penghuni, memantau status kamar, mengelola tagihan, menerima & menindaklanjuti laporan kerusakan, serta menyebarkan pengumuman secara efisien tanpa bergantung pada WhatsApp.

**Penghuni Kos:** Mahasiswa atau pekerja yang tinggal di kos. Mereka membutuhkan akses mudah untuk melihat tagihan, membayar sewa, melaporkan kerusakan di kamar atau fasilitas umum, dan menerima pengumuman dari pengelola — semuanya dalam satu aplikasi yang terorganisir.

### 3. Manfaat Aplikasi

- Menggantikan ketergantungan pada WhatsApp dengan sistem yang terstruktur, terdokumentasi, dan mudah diakses
- Penghuni dapat melaporkan kerusakan dengan mudah dan memantau statusnya secara real-time
- Pemilik kos dapat mengelola data penghuni, kamar, dan tagihan dalam satu dashboard terpadu
- Pengumuman penting tersampaikan ke seluruh penghuni secara merata tanpa khawatir terlewat
- Riwayat pembayaran tersimpan rapi dan dapat dicek kapan saja oleh penghuni maupun pemilik
- Meningkatkan profesionalisme pengelolaan kos dan kepuasan penghuni

### 4. Daftar Fitur Inti

- **Sistem Autentikasi 2 Role** — Login terpisah untuk Pemilik Kos dan Penghuni dengan dashboard yang berbeda
- **Data Penghuni** — Pemilik dapat menambah, mengedit, dan menonaktifkan data penghuni beserta informasi kamar yang ditempati
- **Data Kamar** — Manajemen inventaris kamar (nomor, tipe, harga, status: tersedia/terisi)
- **Laporan Kerusakan** — Penghuni dapat membuat laporan kerusakan dengan deskripsi dan lokasi; pemilik dapat memperbarui status perbaikan (Belum Ditangani 🔴 / Sedang Diperbaiki 🟡 / Selesai 🟢)
- **Pengumuman** — Pemilik dapat memposting pengumuman yang tampil di dashboard seluruh penghuni
- **Tagihan & Pembayaran** — Sistem tagihan bulanan otomatis per penghuni; penghuni dapat mengkonfirmasi pembayaran dan melihat riwayat transaksi
- **Dashboard Role-based** — Dashboard pemilik menampilkan ringkasan hunian, laporan aktif, dan tagihan belum lunas; dashboard penghuni menampilkan status kamar, tagihan, dan laporan pribadi

### 5. Fitur yang Tidak Dikerjakan

- Integrasi payment gateway (transfer otomatis via Midtrans, QRIS, dll)
- Notifikasi push/email untuk pengingat tagihan
- Fitur chat/pesan langsung antara penghuni dan pemilik
- Pengelolaan kontrak sewa digital dan tanda tangan elektronik
- Laporan keuangan & ekspor ke PDF/Excel
- Fitur galeri foto kamar untuk keperluan pemasaran
- Manajemen multi-properti (lebih dari satu lokasi kos)

### 6. Kriteria Aplikasi Dinyatakan Berhasil

- Penghuni dapat membuat laporan kerusakan dan pemilik dapat memperbarui statusnya — status terpantau real-time oleh penghuni
- Alur tagihan berjalan lengkap: pemilik buat tagihan → penghuni konfirmasi bayar → riwayat tercatat
- Dashboard masing-masing role menampilkan data yang relevan dan akurat sesuai akun yang login
- Pengumuman yang diposting pemilik langsung tampil di dashboard semua penghuni
- Data penghuni, kamar, laporan, dan pembayaran tersimpan persisten di database dan tidak hilang saat refresh
- Aplikasi dapat diakses melalui browser (web-based) dan tampil responsif

---

## TEMA 3: CampusCare — Sistem Laporan Fasilitas & Lost and Found Kampus

### 1. Masalah Nyata yang Akan Diselesaikan

Mahasiswa di lingkungan kampus sering menemukan masalah — fasilitas rusak seperti keran bocor, proyektor mati, atau AC tidak berfungsi — namun tidak tahu harus melapor ke mana. Tidak ada kanal resmi yang mudah diakses, sehingga kerusakan dibiarkan begitu saja karena mahasiswa malas melapor secara manual ke bagian administrasi.

Masalah serupa terjadi pada kasus barang hilang dan ditemukan. Saat ini tidak ada sistem terpusat: pengumuman barang hilang/ditemukan hanya mengandalkan story WhatsApp atau tempel kertas di mading yang mudah terlewat. Akibatnya, banyak barang yang ditemukan tidak kembali ke pemiliknya karena tidak ada mekanisme yang menghubungkan pelapor dan penemu secara sistematis.

### 2. Profil Target Pengguna

**Mahasiswa:** Pengguna utama yang dapat membuat laporan fasilitas rusak, melaporkan barang hilang, atau memposting barang yang ditemukan. Mereka butuh antarmuka yang simpel, cepat diakses lewat browser, dan dapat memantau status laporan mereka.

**Admin Kampus/Fasilitas:** Staf yang bertanggung jawab menindaklanjuti laporan kerusakan fasilitas. Mereka butuh dashboard terpusat yang memudahkan monitoring semua laporan masuk, memperbarui status penanganan, dan mengelola verifikasi klaim barang temuan.

### 3. Manfaat Aplikasi

- Mahasiswa memiliki kanal resmi yang mudah diakses untuk melaporkan kerusakan fasilitas kampus
- Admin dapat memantau dan menindaklanjuti laporan secara terpusat, mengurangi kerusakan yang terabaikan
- Sistem Lost & Found digital meningkatkan peluang barang hilang kembali ke pemiliknya melalui pencocokan otomatis berdasarkan kategori, lokasi, dan waktu
- Proses klaim barang temuan lebih terstruktur dan aman dengan verifikasi admin
- Riwayat laporan tersimpan rapi sebagai bukti dan bahan evaluasi manajemen fasilitas kampus
- Meningkatkan keterlibatan mahasiswa dalam menjaga fasilitas kampus secara kolektif

### 4. Daftar Fitur Inti

**Laporan Fasilitas:**
- Buat laporan kerusakan dengan deskripsi, kategori kerusakan, dan pilihan lokasi (gedung & lantai)
- Upload foto sebagai bukti kerusakan
- Tracking status laporan: Belum Ditangani 🔴 / Sedang Diperbaiki 🟡 / Selesai 🟢
- Riwayat laporan yang pernah dibuat oleh mahasiswa

**Lost & Found:**
- Lapor barang hilang (deskripsi, kategori, lokasi terakhir, waktu kehilangan, foto)
- Lapor barang ditemukan (deskripsi, kategori, lokasi penemuan, waktu, foto)
- Sistem pencarian & pencocokan barang berdasarkan kategori, lokasi, dan waktu
- Pengajuan klaim barang oleh pemilik yang merasa barang ditemukan adalah miliknya
- Verifikasi dan persetujuan klaim oleh admin

**Sistem Kampus:**
- Login & register dengan autentikasi role (Mahasiswa & Admin)
- Dashboard mahasiswa: laporan aktif, status terkini, aktivitas Lost & Found
- Dashboard admin: semua laporan masuk, filter status, manajemen klaim
- Notifikasi perubahan status laporan untuk mahasiswa pelapor
- Riwayat aktivitas lengkap per pengguna

### 5. Fitur yang Tidak Dikerjakan

- Notifikasi push/email otomatis ke mahasiswa
- Peta interaktif lokasi kerusakan di dalam kampus
- Sistem poin/reward untuk mendorong partisipasi pelaporan
- Chat langsung antara penemu dan pemilik barang
- Integrasi dengan sistem akademik atau kartu mahasiswa untuk verifikasi identitas
- Laporan statistik & analitik kondisi fasilitas kampus untuk manajemen
- Fitur ekspor laporan ke PDF untuk keperluan rapat/evaluasi

### 6. Kriteria Aplikasi Dinyatakan Berhasil

- Mahasiswa dapat membuat laporan fasilitas rusak dan memantau statusnya — admin dapat memperbarui status dan perubahan terpantau oleh pelapor
- Alur Lost & Found berjalan lengkap: lapor hilang/temuan → pencarian/pencocokan → ajukan klaim → verifikasi admin → status selesai
- Dashboard admin menampilkan seluruh laporan masuk dengan filter status yang berfungsi; dashboard mahasiswa menampilkan data laporan dan aktivitas milik sendiri
- Sistem pencocokan barang hilang & ditemukan berhasil menyarankan kandidat yang relevan berdasarkan kategori dan lokasi
- Aplikasi dapat diakses melalui browser (web-based) dan tampil responsif di berbagai ukuran layar
- Data laporan, status, dan riwayat tersimpan persisten di database dan tidak hilang saat refresh
