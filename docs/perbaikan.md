# Revisi

## Yang di UBAH
###  1. Ubah di bagian "Rentang Anggaran Terpilih"

Gunakan satu garis *track* slider tunggal, bukan dua *bar* terpisah.**

"Ubah kontrol anggaran dari dua slider terpisah (Min dan Max) menjadi satu *dual-thumb range slider* yang terintegrasi (berdasarkan pustaka seperti Radix UI/Shadcn UI).

**Detail Komponen:**

* **Track Tunggal:** Gunakan satu garis *track* horizontal ungu. Area *track* **di antara** kedua *thumb* harus diarsir dengan warna ungu aksen yang solid untuk menunjukkan rentang yang dipilih secara visual. Area di luar rentang tetap berwarna abu-abu gelap/hitam.
* **Dual Thumbs:** Tempatkan dua titik kontrol (*thumb*) ungu pada satu garis *track* tersebut. Satu *thumb* di sisi kiri untuk 'Minimum' dan satu *thumb* di sisi kanan untuk 'Maksimum'.
* **Visual Nilai (Sinkronisasi):**
* Teks di atas *bar* (misalnya 'Rp 1.000.000 s/d Rp 11.000.000') harus diperbarui secara dinamis mengikuti posisi kedua *thumb*.
* Hapus label teks 'Batas Minimum...' dan 'Batas Maksimum...'. Ganti dengan label nilai (seperti balon teks kecil) yang **melayang tepat di atas masing-masing thumb**, menampilkan nilai spesifiknya saat digeser.


* **Tata Letak:** Posisikan satu *bar* terpadu ini di tengah kartu, rapi, dan simetris, memastikan kedua *thumb* tidak bisa saling melewati dalam logika komponen."

### 2. Ubah di bagian "Bagaimana Skenario Penggunaan Utama Anda?" (Langkah 3)

Tolong *refactor* komponen antarmuka "Smart Wizard" pada Langkah 3 (Skenario Pakai) agar menggunakan **Dynamic State Mapping (Conditional Rendering)**.

Saat ini, opsi skenario bersifat statis secara global, sehingga opsi yang tidak relevan (seperti "Fotografi" untuk "TWS") ikut muncul. Saya ingin opsi skenario berubah secara dinamis berdasarkan `selectedCategory` yang dipilih *user* pada Langkah 1.

**1. Buat Data Mapping Object:**
Buat sebuah objek konfigurasi atau *array of objects* yang memetakan kelima kategori gadget dengan skenario spesifiknya masing-masing. Gunakan struktur data berikut sebagai referensi:

```javascript
const scenarioMapping = {
  "Smartphone": [
    { id: "sp_game", title: "Gaming Berat", desc: "Performa GPU tinggi & refresh rate mulus", icon: "Flame" },
    { id: "sp_foto", title: "Fotografi & Kamera", desc: "Sensor jernih, zoom optik, & akurasi warna", icon: "Camera" },
    { id: "sp_sosmed", title: "Sosmed & Hiburan", desc: "Layar cerah, baterai awet, navigasi lancar", icon: "Smartphone" },
    { id: "sp_bisnis", title: "Bisnis & Multitasking", desc: "Keamanan data, memori besar, & performa stabil", icon: "Briefcase" }
  ],
  "Laptop": [
    { id: "lp_game", title: "Gaming & 3D Render", desc: "Kartu grafis diskrit & sistem pendingin maksimal", icon: "Gamepad" },
    { id: "lp_kreatif", title: "Video & Desain Grafis", desc: "Akurasi warna sRGB tinggi & RAM besar", icon: "Palette" },
    { id: "lp_coding", title: "Programming / IT", desc: "Prosesor multi-core kuat & keyboard nyaman", icon: "Code" },
    { id: "lp_office", title: "Office & Mobilitas", desc: "Desain tipis, ringan, & baterai tahan seharian", icon: "Coffee" }
  ],
  "Tablet": [
    { id: "tb_gambar", title: "Ilustrasi & Desain", desc: "Dukungan stylus presisi & layar resolusi tinggi", icon: "PenTool" },
    { id: "tb_catatan", title: "Kuliah & Catatan", desc: "Ringan untuk dibawa, baterai awet untuk kelas", icon: "BookOpen" },
    { id: "tb_nonton", title: "Nonton & Hiburan", desc: "Speaker stereo mantap & layar OLED/AMOLED", icon: "Monitor" },
    { id: "tb_kerja", title: "Pengganti Laptop", desc: "Dukungan keyboard eksternal & mode desktop", icon: "Briefcase" }
  ],
  "TWS / Audio": [
    { id: "au_olahraga", title: "Olahraga & Gym", desc: "Tahan air/keringat (IP Rating) & fitting aman di telinga", icon: "Activity" },
    { id: "au_rapat", title: "Kerja & Rapat Online", desc: "Mikrofon jernih dengan peredam bising (ANC/ENC)", icon: "Mic" },
    { id: "au_musik", title: "Musik / Audiophile", desc: "Kualitas audio Hi-Res & soundstage luas", icon: "Headphones" },
    { id: "au_game", title: "Mobile Gaming", desc: "Mode latensi sangat rendah (low latency)", icon: "Crosshair" }
  ],
  "Smartwatch": [
    { id: "sw_olahraga", title: "Lari & Olahraga Outdoor", desc: "GPS presisi & pelacakan rute akurat", icon: "Map" },
    { id: "sw_sehat", title: "Pantau Kesehatan", desc: "Sensor detak jantung, SpO2, & pemantauan tidur", icon: "Heart" },
    { id: "sw_notif", title: "Ekstensi Smartphone", desc: "Balas pesan cepat & terima telepon dari pergelangan", icon: "MessageSquare" },
    { id: "sw_gaya", title: "Fashion & Gaya Hidup", desc: "Desain premium & kustomisasi watch face beragam", icon: "Watch" }
  ]
};

```

**2. Instruksi Logika Rendering UI:**

* Tangkap *state* dari Langkah 1 (contoh: `category = 'Tablet'`).
* Pada komponen Langkah 3, jangan me-render semua skenario secara *hardcode*. Gunakan `scenarioMapping[category]` untuk merender daftar *card* pilihan secara dinamis (`.map()`).
* Jika *user* menekan tombol 'Kembali' ke Langkah 1 dan mengubah kategori (misal dari Tablet ke TWS), pastikan *state* pilihan skenario di Langkah 3 (jika ada yang sudah terpilih sebelumnya) otomatis di-*reset* atau dikosongkan agar tidak terjadi konflik data pada algoritma *scoring*.

## Yang di PERBAIKI
### 3. Perbaiki text alasan di bagian "Rekomendasi Gadget Paling Cocok untuk Anda"

**Konteks Masalah:**
Pada komponen *Card* "Pilihan Nomor 1" (Best Option), bagian teks alasan/deskripsi me-render format teks mentah yang berisi sintaks Markdown untuk *bold* (misalnya: `**Performa** yang luar biasa`). Saat ini sintaks tersebut tidak ter-render menjadi tulisan tebal (*bold*), melainkan tercetak apa adanya beserta tanda bintangnya.

**Instruksi Perbaikan:**
Tolong perbaiki cara komponen tersebut me-render string deskripsi. Jangan render string tersebut secara mentah. Pilih salah satu dari dua pendekatan berikut yang paling cocok dengan *stack* aplikasi kita (asumsi menggunakan React/Next.js atau Vue):

**Opsi 1: Menggunakan Custom Formatter (Ringan & Tanpa Library Tambahan)**
Buat sebuah *helper function* sederhana untuk mem-parsing sintaks `**teks**` menjadi elemen `<strong>` (atau tag dengan *font-weight bold*) tanpa menggunakan `dangerouslySetInnerHTML` agar tetap aman dari XSS.

*Contoh implementasi untuk React:*

```jsx
// Helper function untuk mem-parsing teks bold markdown
const formatText = (text) => {
  if (!text) return null;
  // Memisahkan string berdasarkan pola **teks**
  const parts = text.split(/(\*\*.*?\*\*)/g);
  
  return parts.map((part, index) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      // Hilangkan bintang dan bungkus dengan tag <strong>
      return <strong key={index} className="font-bold text-white">{part.slice(2, -2)}</strong>;
    }
    return part; // Kembalikan teks biasa
  });
};

// Penggunaan di komponen:
// <p>{formatText("1. **Performa** yang luar biasa")}</p>

```

**Opsi 2: Menggunakan Library Markdown (Jika teks deskripsi punya format yang lebih kompleks)**
Jika data string dari API ke depannya juga akan mengandung *list* markdown (`-`), *italic* (`*`), atau *link* (`[teks](url)`), tolong integrasikan library parser yang aman seperti `react-markdown` (untuk React) atau `marked` / `markdown-it` (untuk Vue) untuk merender bagian deskripsi tersebut.

**Tugas Tambahan (Opsional tapi Penting):**
Tolong tambahkan juga penanganan *error fallback* pada gambar produk di kiri atas (gambar `iPad Air M2`). Saat ini URL gambarnya *broken* (menampilkan *alt text* dan ikon gambar pecah). Buat fungsi `onError` pada tag `<img>` untuk menggantinya dengan gambar *placeholder* default jika *link* gambar dari *database* tidak bisa dimuat.

## Yang di TAMBAHKAN
### 4. Tambahkan gambar produk nyata pada card 'Pilihan Nomor 1' dan 'Alternatif Peringkat Selanjutnya'

Tolong perbaiki bagian *thumbnail* gambar pada komponen Card 'Pilihan Nomor 1' dan 'Alternatif Peringkat Selanjutnya'. Saat ini gambar gagal dimuat (*broken image link*) dan hanya menampilkan *alt text*. Saya ingin menampilkan **foto produk asli (real photo)**, bukan sekadar *icon* SVG statis atau gambar yang rusak.

Tolong implementasikan 3 hal berikut pada komponen tersebut:

**1. Validasi Data Source (Binding Image):**
Pastikan atribut `src` pada elemen `<img>` (atau komponen `<Image/>` jika menggunakan Next.js) sudah diarahkan ke *field* yang tepat dari *response* API (contoh: `product.imageUrl` atau `product.thumbnail_url`). Pastikan database atau API kita benar-benar menyimpan URL foto produk asli dengan format JPG, PNG, atau WEBP.

**2. Styling Gambar (Object Fit):**
Tambahkan *styling* agar foto produk asli (yang mungkin memiliki rasio bervariasi) bisa dirender dengan rapi tanpa terlihat lonjong atau gepeng.

* Gunakan properti CSS `object-fit: contain;` (jika pakai Tailwind: `object-contain`).
* Pastikan kontainer *wrapper* gambarnya memiliki *width* dan *height* absolut (misalnya `w-24 h-24`), serta berikan latar belakang (*background*) yang netral (seperti warna putih atau transparan) agar perangkat berlatar putih menyatu dengan rapi.

**3. Implementasi Fallback Image (Error Handling):**
Wajib tambahkan fungsi penanganan *error* (event `onError`) pada tag gambar. Jika link foto utama dari database ternyata rusak/mati, antarmuka tidak boleh menampilkan ikon 'gambar pecah'. Otomatis gantikan dengan gambar *placeholder* default (misalnya siluet gadget yang rapi atau logo aplikasi).

*Contoh implementasi ringan (React + Tailwind):*

```jsx
<div className="w-24 h-24 flex-shrink-0 bg-white rounded-md overflow-hidden">
  <img 
    src={product.imageUrl || '/default-placeholder.jpg'} 
    alt={product.name} 
    className="w-full h-full object-contain"
    onError={(e) => {
      e.target.onerror = null; // Mencegah infinite loop
      e.target.src = '/default-placeholder.jpg'; // Ganti dengan gambar cadangan di folder public
    }}
  />
</div>
```"

```