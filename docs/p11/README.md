# Tugas P11 — CompareBuy v1.1.0

Issue fokus: [#17 — skor katalog nol dianggap kosong](https://github.com/FirmanFelixNduru/RPLWeb/issues/17).

## Branch dan perubahan

| Branch | Peran |
| --- | --- |
| `v1.0` | Baseline stabil pada `779ed35e8ca5c951ef720804e55527b14e9ab3e0` |
| `v1.0_dev` | Pengembangan, unit test, dan deployment preview untuk testing |
| `V1.1` | Rilis versi `1.1.0` setelah alur pengembangan hijau |

Bug: `getCatalogScore` sebelumnya menggunakan `|| 50`. Lima skor bernilai `0`
menghasilkan skor kartu `50`, padahal seharusnya `0`. Satu dimensi `0` dengan
empat dimensi belum tersedia seharusnya `40`, bukan `50`. Backend memang menerima
skor sah 0–100. Perbaikannya menggunakan `?? 50`, sehingga hanya nilai
`null`/`undefined` yang menggunakan default netral. Perubahan perilaku aplikasi
difokuskan pada bug ini; perubahan lain mendukung pengujian, CI/CD, dan bukti tugas.

## 200 unit test

| Kelompok | Jumlah |
| --- | ---: |
| Pengujian frontend sebelumnya, termasuk ekspektasi skor nol yang dikoreksi | 105 |
| Kontrak skor, default, dimensi, dan pembulatan | 20 |
| Validasi data dock, duplikasi, dan batas kapasitas | 20 |
| Interaksi preset anggaran untuk lima kategori | 15 |
| Pencarian, filter, sorting, dan pagination pada API fallback | 20 |
| Urutan, unit spesifikasi, highlight, dan kategori perbandingan | 20 |
| **Total** | **200** |

Seluruh pengujian ini berjalan pada Node.js dengan mock untuk jaringan, storage,
hook, dan waktu bila diperlukan. Tidak mengakses PostgreSQL atau marketplace.
Tes integrasi backend dan smoke test HTTP tidak dimasukkan ke angka 200.
Setiap kasus parameter menghasilkan test yang terhitung sendiri; assertion di
dalam satu test tidak dihitung sebagai test tambahan.

Jalankan dari root repositori:

```powershell
npm ci --prefix frontend --no-audit --no-fund
npm run test:ci --prefix frontend
npm run lint --prefix frontend
```

Runner menyimpan `summary.json`, `unit-tests.tap`, dan `junit.xml` di
`frontend/reports/`. Gate menolak kurang dari 200 test, kegagalan, cancelled,
skipped, atau todo. Folder report lokal tidak di-commit; salinan artefak CI
pilihan disimpan pada `evidence/` untuk reviewer.

## Bukti merah → hijau

| Tahap | Commit | Hasil aktual |
| --- | --- | --- |
| [Merah / run #1](https://github.com/FirmanFelixNduru/RPLWeb/actions/runs/44587150727) | `2b3d40f` | 200 total: 198 passed, 2 failed, 0 skipped; build/deploy/smoke **skipped** |
| [Percobaan deploy #2](https://github.com/FirmanFelixNduru/RPLWeb/actions/runs/44587976559) | `cc5f06f` | 200 passed dan build berhasil; deploy menemukan referensi dependensi runtime yang belum dipindahkan |
| [Percobaan deploy #3](https://github.com/FirmanFelixNduru/RPLWeb/actions/runs/44588371623) | `266dd87` | 200 passed dan build berhasil; deploy menemukan referensi `.next` yang belum dipindahkan |
| [Hijau lengkap / run #4](https://github.com/FirmanFelixNduru/RPLWeb/actions/runs/44588874241) | `7f576ad` | **200 passed, 0 failed, 0 skipped; build, deploy, dan smoke test semuanya berhasil** |

Tahap merah memakai bug asli, bukan assertion `false`, pemalsuan hasil, penghapusan
test, atau pengubahan batas agar test lolos. Kedua failure membuktikan kesalahan
skor yang sama. Perbaikan kode dilakukan setelah run merah selesai direkam.
Kegagalan infrastruktur pada dua percobaan deploy dilaporkan terpisah dari
demonstrasi unit test merah, lalu diselesaikan dengan pemindahan workspace build
yang lengkap serta pemulihan dependensi dari lockfile.

Efek test gagal: proses unit test keluar dengan kode 1, job turunan tidak
berjalan, dan commit gagal tidak dipublikasikan. Situs produksi tetap pada versi
terakhir yang berhasil. Bukti hasil job tersedia di [red-run.json](evidence/red-run.json)
dan [green-run.json](evidence/green-run.json).

## CI/CD otomatis

Workflow: [p11.yml](../../.github/workflows/p11.yml).

```text
push v1.0_dev / V1.1 / main
  → npm ci → minimal 200 unit test tanpa failure/skip → lint
  → Vercel build
  → paket output prebuilt + file .next yang dirujuk
  → deploy --prebuilt dari artefak commit yang sama
  → verifikasi /version.json serta empat route aplikasi
```

Job build bergantung pada unit-tests, deploy bergantung pada build, dan smoke
bergantung pada deploy. Deploy langsung dari integrasi Git Vercel dinonaktifkan
melalui `frontend/vercel.json`, sehingga tidak melewati gate Actions.
`v1.0_dev` menghasilkan preview; `V1.1` dan `main` menghasilkan production.
Pull request hanya menjalankan unit test/lint, tanpa publikasi.

Secret tersedia di GitHub, tanpa nilai secret disimpan dalam kode, screenshot,
laporan, atau artefak pengujian:

- `VERCEL_TOKEN`: token khusus proyek CompareBuy, masa berlaku 30 hari.
- `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`.
- `VERCEL_AUTOMATION_BYPASS_SECRET`: untuk smoke test terhadap URL preview yang
  dilindungi Vercel Authentication; perlindungan proyek tetap aktif.

Repository variable publik `NEXT_PUBLIC_API_URL` menyimpan URL backend.
CI menyalurkan nilai publik tersebut ke environment build secara eksplisit,
karena pembacaan variable bertipe sensitive melalui Vercel dapat menghasilkan
placeholder `[SENSITIVE]`. Build ditolak jika placeholder masuk ke bundle atau
URL backend tidak ditemukan. Smoke test juga memeriksa konfigurasi pada chunk
JavaScript katalog yang benar-benar dipublikasikan. Nilai private lain tidak
diubah atau dicetak.

Token deployment perlu dirotasi sebelum kedaluwarsa agar deployment berikutnya
tetap berjalan. Node.js 24 dan Vercel CLI 66.2.0 digunakan pada pipeline ini.
Warning `<img>` yang telah ada tidak diperlakukan sebagai kegagalan lint.

## Live dan verifikasi rilis

- Produksi: https://comparebuy-livid.vercel.app
- [Preview yang telah diverifikasi](https://comparebuy-6r1e2kmxj-firmanfelixnduru.vercel.app).
- [Bukti smoke preview](evidence/preview-smoke/smoke.json): HTTP 200 untuk
  `/version.json`, `/`, `/catalog`, `/wizard`, dan `/compare`; commit live cocok
  dengan `7f576addfb7563a7759fc1e817b051962a302d4c`.
- [Pipeline rilis V1.1](https://github.com/FirmanFelixNduru/RPLWeb/actions?query=branch%3AV1.1).
- [Rilis v1.1.0 dan lampiran bukti produksi](https://github.com/FirmanFelixNduru/RPLWeb/releases/tag/v1.1.0).

Preview memerlukan akses Vercel; URL produksi digunakan reviewer untuk pengujian
publik. Saat pemeriksaan browser, katalog preview menggunakan fallback lokal
karena origin preview tidak termasuk origin backend yang diizinkan. Hal ini
tidak dihitung sebagai bukti integrasi backend berhasil; URL produksi digunakan
untuk pemeriksaan koneksi API. Smoke test memeriksa HTTP dan identitas commit, bukan menggantikan
pengujian interaksi pengguna. Bukti produksi final, screenshot live, dan hasil
pipeline rilis dilampirkan pada GitHub Release agar tetap merujuk commit aplikasi
yang diuji tanpa mengubahnya hanya untuk menambahkan bukti sesudah deployment.

## Screenshot progres yang sebenarnya

| File | Bukti |
| --- | --- |
| [00-baseline-branch.png](screenshots/00-baseline-branch.png) | Branch baseline `v1.0` |
| [01-baseline-live.png](screenshots/01-baseline-live.png) | Aplikasi produksi sebelum rilis P11 |
| [02-pipeline-progress.png](screenshots/02-pipeline-progress.png) | Pipeline sedang berjalan: 200 test sudah lulus, build sedang berlangsung |
| [03-red-pipeline-full.png](screenshots/03-red-pipeline-full.png) | Dua test gagal dan job build/deploy/smoke dilewati |
| [04-first-deploy-failure.png](screenshots/04-first-deploy-failure.png) | Kendala pemindahan artefak pada percobaan deploy awal |
| [05-green-build-deploy.png](screenshots/05-green-build-deploy.png) | Alur pengembangan hijau lengkap, termasuk jumlah test dan deployment |

Screenshot merupakan tangkapan halaman GitHub/aplikasi asli melalui Orca, tanpa
rekayasa tampilan atau pengubahan angka. File JSON pendamping mencatat URL dan
waktu pengambilan. Waktu artefak CI menggunakan UTC; tambahkan 7 jam untuk WIB.
Screenshot rilis dan aplikasi produksi final tersedia pada lampiran GitHub Release.
