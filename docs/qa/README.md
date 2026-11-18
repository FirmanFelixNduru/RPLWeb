# Laporan bug setelah deployment CompareBuy

Pengujian awal dilakukan pada https://comparebuy-livid.vercel.app dengan backend
https://comparebuy-api.onrender.com. Baseline kode: `2a89ad8`.
Setiap baris di bawah merupakan bug yang berhasil direproduksi, bukan daftar dugaan.

| Issue | Permasalahan | Perbaikan |
| --- | --- | --- |
| [#5](https://github.com/FirmanFelixNduru/RPLWeb/issues/5) | Kategori wizard tidak dapat dipilih dengan keyboard | Tombol native, fokus terlihat, dan status pilihan |
| [#6](https://github.com/FirmanFelixNduru/RPLWeb/issues/6) | Menu mobile tidak mengumumkan status buka/tutup | `aria-expanded`, `aria-controls`, dan landmark navigasi |
| [#7](https://github.com/FirmanFelixNduru/RPLWeb/issues/7) | Label anggaran membulatkan nilai secara keliru | Jumlah rupiah lengkap pada preset dan tooltip |
| [#8](https://github.com/FirmanFelixNduru/RPLWeb/issues/8) | Slider tidak mendukung preset Rp300 ribu | Step Rp100 ribu dan batas jarak slider yang konsisten |
| [#9](https://github.com/FirmanFelixNduru/RPLWeb/issues/9) | Skenario kosong tetap bisa dilanjutkan | Validasi minimal satu skenario dan pesan error |
| [#10](https://github.com/FirmanFelixNduru/RPLWeb/issues/10) | Slider prioritas tidak memiliki nama aksesibel | Label terkait dengan ID setiap slider |
| [#11](https://github.com/FirmanFelixNduru/RPLWeb/issues/11) | Spasi luar pencarian menghilangkan hasil yang valid | Normalisasi kata pencarian di katalog dan fallback API |
| [#12](https://github.com/FirmanFelixNduru/RPLWeb/issues/12) | Fallback membalik urutan kolom perbandingan | Ambil produk sesuai urutan ID pilihan |
| [#13](https://github.com/FirmanFelixNduru/RPLWeb/issues/13) | Respons lama mengisi matriks yang telah dikosongkan | Abaikan respons setelah pilihan berubah atau halaman ditutup |
| [#14](https://github.com/FirmanFelixNduru/RPLWeb/issues/14) | Data dock tersimpan yang tidak valid merusak halaman | Validasi array/produk, deduplikasi, dan batas empat produk |

## Bukti dan pengujian

- [before.json](before.json): sepuluh kasus gagal pada deployment awal.
- [local-after.json](local-after.json): sepuluh kasus lulus pada build produksi lokal setelah perbaikan.
- [issues.json](issues.json): pemetaan kasus, nomor issue, dan file sumber.
- `npm test --prefix frontend`: 105 pengujian lulus, termasuk enam regresi baru untuk penyimpanan, fallback, dan respons asinkron.
- `npm run build --prefix frontend`: berhasil.
- `npm run lint --prefix frontend`: tanpa error; delapan warning penggunaan `<img>` yang sudah ada tetap tersedia.

Laporan browser mencatat waktu UTC. Pemeriksaan gangguan API dan respons terlambat
menggunakan intersepsi `fetch` pada tab uji saja. Pengujian tersebut tidak menyatakan
bahwa backend mengalami gangguan saat pengujian berlangsung. Pemeriksaan label
aksesibilitas memeriksa DOM/semantik; bukan pengujian ucapan dengan pembaca layar.

## Mengulangi pengujian deployment

Prasyarat: Python 3, CLI Orca, dan aplikasi Orca aktif. Jalankan dari root repositori:

```powershell
python docs/qa/browser_audit.py --base-url https://comparebuy-livid.vercel.app --output docs/qa/production-after.json
```

Untuk build lokal, ganti `--base-url` dengan alamat server lokal. Script mengambil
fixture produk dari API produksi melalui HTTP, membuka tab uji, menyimulasikan
gangguan pada tab tersebut, dan memulihkan key dock semula setelah selesai.

Issue ditutup setelah verifikasi deployment perbaikan, dengan komentar berisi
PR/commit, waktu uji, hasil aktual, dan bukti kasus terkait.
