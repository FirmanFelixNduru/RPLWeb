/**
 * CompareBuy — Curated Product Dataset (Frontend Seed & Offline Fallback)
 * 20 products across 5 categories matching backend specifications.
 */

export const PRODUCTS = [
  // ── SMARTPHONES ──
  {
    id: "sm-001",
    name: "Samsung Galaxy S24 Ultra",
    brand: "Samsung",
    category: "smartphone",
    price: 19999000,
    image: "https://images.unsplash.com/photo-1610945265064-0e34e5519bbf?w=600&auto=format&fit=crop&q=80",
    description: "Flagship Samsung dengan S Pen, kamera 200MP, dan layar Dynamic AMOLED 2X terbaik di kelasnya.",
    specs: {
      display: "6.8\" Dynamic AMOLED 2X, 3120x1440",
      processor: "Snapdragon 8 Gen 3 (4nm)",
      ram: "12 GB LPDDR5X",
      storage: "256 GB / 512 GB / 1 TB UFS 4.0",
      battery: "5000 mAh (45W Fast Charging)",
      camera: "200MP + 50MP (5x Periscope) + 12MP (Ultrawide) + 10MP (3x Tele)",
      os: "Android 14 (One UI 6.1) - 7 Tahun Update",
      weight: "232g",
      connectivity: "5G, Wi-Fi 7, Bluetooth 5.3, UWB, NFC",
      refresh_rate: "1-120Hz LTPO Adaptive",
      resolution: "3120 x 1440 (QHD+)",
      water_resistance: "IP68 (1.5m hingga 30 menit)",
      build_material: "Titanium Frame, Corning Gorilla Armor",
      special_features: "Built-in S Pen, Galaxy AI Live Translate, Circle to Search"
    },
    review_sentiment: {
      overall_score: 4.6,
      total_reviews: 12840,
      pros: [
        "Kamera zoom 100x & 5x optik luar biasa tajam",
        "S Pen terintegrasi sangat membantu produktivitas",
        "Layar Gorilla Armor minim refleksi cahaya silau",
        "Galaxy AI sangat berguna di aktivitas harian",
        "Daya tahan baterai kuat tembus 1.5 hari pemakaian normal"
      ],
      cons: [
        "Dimensi bodi cukup bongsor dan bersudut tajam",
        "Harga sangat premium di atas 19 jutaan",
        "Kecepatan charging 45W masih kalah dibanding rival Tiongkok"
      ],
      summary: "Pilihan utama Android kelas atas untuk power-user, profesional, dan pecinta fotografi jarak jauh."
    },
    warranty: {
      duration_months: 12,
      coverage: "Garansi Resmi SEIN (Samsung Electronics Indonesia) — Perlindungan penuh hardware & software",
      claim_ease: 8,
      official_service_centers: 350,
      score: 82.0
    },
    marketplace_links: {
      tokopedia: "https://www.tokopedia.com/search?q=samsung+galaxy+s24+ultra",
      shopee: "https://shopee.co.id/search?keyword=samsung+galaxy+s24+ultra",
      lazada: "https://www.lazada.co.id/catalog/?q=samsung+galaxy+s24+ultra"
    },
    tags: ["flagship", "s-pen", "200mp", "ai", "titanium", "5g"],
    release_year: 2024,
    score_performance: 95,
    score_camera: 98,
    score_battery: 80,
    score_display: 97,
    score_build_quality: 95,
    score_value: 60,
    score_audio: 82,
    score_software: 88
  },
  {
    id: "sm-002",
    name: "iPhone 15 Pro Max",
    brand: "Apple",
    category: "smartphone",
    price: 22499000,
    image: "https://images.unsplash.com/photo-1695048133142-1a20484d2569?w=600&auto=format&fit=crop&q=80",
    description: "iPhone tercanggih dengan rangka titanium kelas dirgantara, chip A17 Pro 3nm, dan kamera telefoto 5x.",
    specs: {
      display: "6.7\" Super Retina XDR OLED, 2796x1290",
      processor: "Apple A17 Pro (3nm)",
      ram: "8 GB Unified",
      storage: "256 GB / 512 GB / 1 TB NVMe",
      battery: "4441 mAh (MagSafe 15W)",
      camera: "48MP Utama + 12MP Ultrawide + 12MP Periscope Telefoto 5x",
      os: "iOS 17 (Dukungan Apple Intelligence)",
      weight: "221g",
      connectivity: "5G, Wi-Fi 6E, Bluetooth 5.3, UWB Gen 2, USB-C 3.0",
      refresh_rate: "1-120Hz ProMotion Adaptive",
      resolution: "2796 x 1290",
      water_resistance: "IP68 (6m hingga 30 menit)",
      build_material: "Grade 5 Titanium Frame, Ceramic Shield Depan",
      special_features: "Action Button yang dapat dikustomisasi, Port USB-C 10Gbps, ProRes Video Recording"
    },
    review_sentiment: {
      overall_score: 4.7,
      total_reviews: 18920,
      pros: [
        "Performa grafis chip A17 Pro sanggup jalankan game konsol AAA",
        "Kamera perekaman video stabil terbaik di industri",
        "Transisi ke port USB-C mempermudah transfer data cepat",
        "Bobot lebih ringan signifikan berkat rangka titanium",
        "Ekosistem iOS & Apple Watch sangat mulus tanpa lag"
      ],
      cons: [
        "Harga tertinggi di antara semua smartphone komersial",
        "Kecepatan pengisian daya standar (sekitar 20W)",
        "Kepala charger dan casing tidak disertakan dalam kotak penjualan"
      ],
      summary: "Pilihan mutlak bagi kreator konten video profesional dan pengguna loyal ekosistem Apple."
    },
    warranty: {
      duration_months: 12,
      coverage: "Garansi Resmi iBox / Digimap / GDN Indonesia — Layanan perbaikan Apple Authorized Service Provider",
      claim_ease: 9,
      official_service_centers: 45,
      score: 88.0
    },
    marketplace_links: {
      tokopedia: "https://www.tokopedia.com/search?q=iphone+15+pro+max",
      shopee: "https://shopee.co.id/search?keyword=iphone+15+pro+max",
      lazada: "https://www.lazada.co.id/catalog/?q=iphone+15+pro+max"
    },
    tags: ["flagship", "titanium", "a17-pro", "5g", "ios", "periscope"],
    release_year: 2023,
    score_performance: 97,
    score_camera: 94,
    score_battery: 78,
    score_display: 95,
    score_build_quality: 96,
    score_value: 55,
    score_audio: 85,
    score_software: 95
  },
  {
    id: "sm-003",
    name: "Google Pixel 8 Pro",
    brand: "Google",
    category: "smartphone",
    price: 14999000,
    image: "https://images.unsplash.com/photo-1598327105666-5b89351aff97?w=600&auto=format&fit=crop&q=80",
    description: "Smartphone AI-first dari Google dengan kamera komputasional juara dunia dan jaminan 7 tahun OS update.",
    specs: {
      display: "6.7\" Super Actua LTPO OLED, 2992x1344",
      processor: "Google Tensor G3 (Titan M2 Security)",
      ram: "12 GB LPDDR5X",
      storage: "128 GB / 256 GB / 512 GB UFS 3.1",
      battery: "5050 mAh (30W Fast Charging)",
      camera: "50MP Utama OIS + 48MP Ultrawide Macro + 48MP Telefoto 5x",
      os: "Android 14 Murni (Pixel Experience)",
      weight: "213g",
      connectivity: "5G, Wi-Fi 7, Bluetooth 5.3, UWB, NFC",
      refresh_rate: "1-120Hz LTPO",
      resolution: "2992 x 1344",
      water_resistance: "IP68",
      build_material: "Bingkai Aluminium Polish, Corning Gorilla Glass Victus 2",
      special_features: "Sensor Suhu Objek, Best Take, Magic Audio Eraser, Video Boost"
    },
    review_sentiment: {
      overall_score: 4.4,
      total_reviews: 6730,
      pros: [
        "Hasil jepretan foto still natural terbaik dengan dynamic range luas",
        "Pengalaman software Android murni tanpa iklan atau bloatware",
        "Dukungan pembaruan OS dan patch keamanan terjamin 7 tahun penuh",
        "Fitur AI eksklusif seperti Audio Magic Eraser dan Call Screen"
      ],
      cons: [
        "Chipset Tensor G3 cenderung hangat saat bermain game berat lama",
        "Unit resmi tidak dirilis langsung oleh distributor lokal Indonesia",
        "Kecepatan fingerprint scanner dalam layar rata-rata"
      ],
      summary: "Smartphone idaman para fotografer mobile dan purist Android yang menginginkan fitur AI terdepan."
    },
    warranty: {
      duration_months: 12,
      coverage: "Garansi Distributor / Impor Terdaftar IMEI Kemenperin",
      claim_ease: 5,
      official_service_centers: 10,
      score: 58.0
    },
    marketplace_links: {
      tokopedia: "https://www.tokopedia.com/search?q=google+pixel+8+pro",
      shopee: "https://shopee.co.id/search?keyword=google+pixel+8+pro",
      lazada: "https://www.lazada.co.id/catalog/?q=google+pixel+8+pro"
    },
    tags: ["ai-camera", "stock-android", "7yr-update", "5g", "flagship"],
    release_year: 2023,
    score_performance: 80,
    score_camera: 96,
    score_battery: 82,
    score_display: 90,
    score_build_quality: 82,
    score_value: 75,
    score_audio: 78,
    score_software: 98
  },
  {
    id: "sm-004",
    name: "Xiaomi 14 Ultra",
    brand: "Xiaomi",
    category: "smartphone",
    price: 14999000,
    image: "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=600&auto=format&fit=crop&q=80",
    description: "Kamera profesional berbentuk smartphone dengan sensor raksasa Sony LYT-900 1 inci dan optik Leica Summilux.",
    specs: {
      display: "6.73\" LTPO AMOLED C8, 3200x1440 3000nits",
      processor: "Snapdragon 8 Gen 3",
      ram: "16 GB LPDDR5X",
      storage: "512 GB UFS 4.0",
      battery: "5000 mAh (90W HyperCharge, 80W Wireless)",
      camera: "50MP (1\" LYT-900 Stepless f/1.63-f/4.0) + 50MP Tele 3.2x + 50MP Periscope 5x + 50MP Ultrawide",
      os: "Xiaomi HyperOS (Android 14)",
      weight: "227g",
      connectivity: "5G, Wi-Fi 7, Bluetooth 5.4, Dual SIM",
      refresh_rate: "1-120Hz LTPO",
      resolution: "3200 x 1440 (2K WQHD+)",
      water_resistance: "IP68",
      build_material: "Aluminium CNC unibody, Kulit Vegan Nano-Tech",
      special_features: "Diafragma Mekanikal Berubah-ubah, Aksesoris Photography Kit Grip, Perekaman 8K Log"
    },
    review_sentiment: {
      overall_score: 4.5,
      total_reviews: 4280,
      pros: [
        "Sensor 1 inci menghasilkan efek bokeh optik asli tanpa rekayasa software",
        "Karakter warna Leica Authentic yang sangat dramatis dan artistik",
        "Pengisian daya 90W super cepat (0-100% di bawah 35 menit)",
        "Dukungan RAM 16GB dan pendingin Dual-Channel IceLoop yang stabil"
      ],
      cons: [
        "Modul kamera belakang sangat tebal menyerupai lensa kamera pocket",
        "Antarmuka HyperOS masih memuat beberapa notifikasi aplikasi bawaan",
        "Photography Grip Kit dijual terpisah dengan harga lumayan tinggi"
      ],
      summary: "Gadget impian fotografer sejati yang membutuhkan kendali optikal manual dalam genggaman saku."
    },
    warranty: {
      duration_months: 12,
      coverage: "Garansi Resmi Xiaomi Indonesia 15 Bulan + Layanan VIP Pick-up Service",
      claim_ease: 7,
      official_service_centers: 280,
      score: 74.0
    },
    marketplace_links: {
      tokopedia: "https://www.tokopedia.com/search?q=xiaomi+14+ultra",
      shopee: "https://shopee.co.id/search?keyword=xiaomi+14+ultra",
      lazada: "https://www.lazada.co.id/catalog/?q=xiaomi+14+ultra"
    },
    tags: ["leica", "1-inch-sensor", "flagship", "5g", "photography"],
    release_year: 2024,
    score_performance: 94,
    score_camera: 97,
    score_battery: 81,
    score_display: 93,
    score_build_quality: 88,
    score_value: 72,
    score_audio: 80,
    score_software: 78
  },
  {
    id: "sm-005",
    name: "POCO X6 Pro 5G",
    brand: "POCO",
    category: "smartphone",
    price: 3999000,
    image: "https://images.unsplash.com/photo-1567581935884-3349723552ca?w=600&auto=format&fit=crop&q=80",
    description: "Performa monster termurah dengan chipset MediaTek Dimensity 8300-Ultra, layar CrystalRes 120Hz, dan 67W Turbo.",
    specs: {
      display: "6.67\" Flow AMOLED 1.5K, 2712x1220 1800nits",
      processor: "MediaTek Dimensity 8300-Ultra (4nm)",
      ram: "12 GB LPDDR5X",
      storage: "512 GB UFS 4.0",
      battery: "5000 mAh (67W Turbo Charge)",
      camera: "64MP OIS + 8MP Ultrawide + 2MP Macro",
      os: "Xiaomi HyperOS (Android 14)",
      weight: "186g",
      connectivity: "5G, Wi-Fi 6, Bluetooth 5.4, NFC, IR Blaster",
      refresh_rate: "120Hz",
      resolution: "2712 x 1220 (1.5K)",
      water_resistance: "IP54 (Tahan cipratan air)",
      build_material: "Rangka Polikarbonat, Corning Gorilla Glass 5",
      special_features: "LiquidCool Technology 2.0, In-Display Fingerprint, Dual Stereo Speakers Dolby Atmos"
    },
    review_sentiment: {
      overall_score: 4.3,
      total_reviews: 8950,
      pros: [
        "Skor AnTuTu tembus 1.4 juta di harga under 4 juta — value tak tertandingi",
        "Storage internal 512GB UFS 4.0 luar biasa lapang untuk install banyak game",
        "Layar 1.5K tajam dengan bezel sangat tipis",
        "Pengisi daya 67W disertakan langsung dalam paket pembelian"
      ],
      cons: [
        "Kamera sekunder 8MP & 2MP hanya seadanya dalam kondisi minim cahaya",
        "Material bodi plastik tidak semewah ponsel metal kaca",
        "Terdapat bloatware yang perlu dinonaktifkan secara manual"
      ],
      summary: "Ponsel gaming budget terbaik bagi pelajar, mahasiswa, dan gamer kompetitif dengan anggaran terbatas."
    },
    warranty: {
      duration_months: 12,
      coverage: "Garansi Resmi Xiaomi/POCO Indonesia 15 Bulan",
      claim_ease: 7,
      official_service_centers: 280,
      score: 74.0
    },
    marketplace_links: {
      tokopedia: "https://www.tokopedia.com/search?q=poco+x6+pro",
      shopee: "https://shopee.co.id/search?keyword=poco+x6+pro",
      lazada: "https://www.lazada.co.id/catalog/?q=poco+x6+pro"
    },
    tags: ["mid-range", "gaming", "5g", "value", "fast-charging"],
    release_year: 2024,
    score_performance: 82,
    score_camera: 65,
    score_battery: 85,
    score_display: 84,
    score_build_quality: 62,
    score_value: 95,
    score_audio: 68,
    score_software: 70
  },
  {
    id: "sm-006",
    name: "Samsung Galaxy A55 5G",
    brand: "Samsung",
    category: "smartphone",
    price: 5499000,
    image: "https://images.unsplash.com/photo-1580910051074-3eb694886505?w=600&auto=format&fit=crop&q=80",
    description: "Pilihan paling seimbang dengan rangka metal premium, sertifikasi IP67 tahan air, dan update OS hingga 4 tahun.",
    specs: {
      display: "6.6\" Super AMOLED FHD+, 2340x1080 1000nits",
      processor: "Exynos 1480 dengan GPU AMD Xclipse 530",
      ram: "8 GB / 12 GB",
      storage: "128 GB / 256 GB + MicroSD hingga 1TB",
      battery: "5000 mAh (25W Charging)",
      camera: "50MP OIS + 12MP Ultrawide + 5MP Macro",
      os: "Android 14 (One UI 6.1) - 4x Upgrade OS",
      weight: "213g",
      connectivity: "5G, Wi-Fi 6, Bluetooth 5.3, NFC, eSIM",
      refresh_rate: "120Hz",
      resolution: "2340 x 1080 (FHD+)",
      water_resistance: "IP67 (Kedalaman 1m hingga 30 menit)",
      build_material: "Frame Aluminium Solid, Gorilla Glass Victus+ Depan/Belakang",
      special_features: "Samsung Knox Vault Hardware-level, Nightography, Stereo Speakers"
    },
    review_sentiment: {
      overall_score: 4.3,
      total_reviews: 9800,
      pros: [
        "Desain kokoh berbingkai logam terasa seperti ponsel flagship",
        "Sertifikasi tahan air dan debu IP67 memberikan rasa aman maksimal",
        "Jaminan 4 tahun update Android dan 5 tahun patch keamanan",
        "Layar Super AMOLED dengan reproduksi warna cerah dan tajam"
      ],
      cons: [
        "Kecepatan cas terbatas di 25W dan adaptor kepala cas tidak disertakan",
        "Bezel layar sedikit lebih tebal dibandingkan model pesaing",
        "Bobot 213 gram cukup berbobot di saku celana"
      ],
      summary: "Ponsel harian paling awet dan terpercaya untuk pemakaian jangka panjang 3-5 tahun ke depan."
    },
    warranty: {
      duration_months: 12,
      coverage: "Garansi Resmi SEIN Indonesia dengan jaringan 350+ service center",
      claim_ease: 8,
      official_service_centers: 350,
      score: 82.0
    },
    marketplace_links: {
      tokopedia: "https://www.tokopedia.com/search?q=samsung+galaxy+a55+5g",
      shopee: "https://shopee.co.id/search?keyword=samsung+galaxy+a55+5g",
      lazada: "https://www.lazada.co.id/catalog/?q=samsung+galaxy+a55+5g"
    },
    tags: ["mid-range", "5g", "ip67", "amoled", "long-update"],
    release_year: 2024,
    score_performance: 72,
    score_camera: 72,
    score_battery: 82,
    score_display: 82,
    score_build_quality: 80,
    score_value: 85,
    score_audio: 70,
    score_software: 85
  },

  // ── LAPTOPS ──
  {
    id: "lp-001",
    name: "MacBook Air M3",
    brand: "Apple",
    category: "laptop",
    price: 18499000,
    image: "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=600&auto=format&fit=crop&q=80",
    description: "Laptop ultraportable terpopuler di dunia dengan arsitektur chip M3 3nm, desain tanpa kipas (hening total), dan baterai 18 jam.",
    specs: {
      display: "13.6\" Liquid Retina IPS, 2560x1664 500nits",
      processor: "Apple M3 (8-Core CPU, 10-Core GPU, 16-Core Neural Engine)",
      ram: "8 GB / 16 GB Unified Memory",
      storage: "256 GB / 512 GB SSD Super Cepat",
      battery: "52.6 Wh (Hingga 18 jam pemakaian browsing/video)",
      camera: "1080p FaceTime HD dengan komputasi ISP canggih",
      os: "macOS Sonoma (Mendukung Apple Intelligence)",
      weight: "1.24 kg",
      connectivity: "Wi-Fi 6E, Bluetooth 5.3, 2x Thunderbolt / USB 4, MagSafe 3",
      screen_size: "13.6 inch",
      resolution: "2560 x 1664",
      build_material: "100% Aluminium Daur Ulang Anodized",
      special_features: "Desain Fanless Tanpa Kipas Hening 100%, Touch ID, Speaker Spatial Audio 4-Unit"
    },
    review_sentiment: {
      overall_score: 4.7,
      total_reviews: 15200,
      pros: [
        "Efisiensi energi luar biasa, sanggup dipakai kerja seharian tanpa colok charger",
        "Tanpa kipas pendingin sehingga tidak ada suara berisik debu",
        "Trackpad Force Touch dan keyboard Magic Keyboard paling nyaman di dunia laptop",
        "Kualitas audio speaker jernih menggelegar untuk ukuran laptop setipis 11mm"
      ],
      cons: [
        "Varian dasar 8GB RAM kurang ideal untuk beban kerja rendering 3D berat berkelanjutan",
        "Pilihan port kabel hanya 2 buah USB-C di sisi kiri",
        "Komponen internal RAM dan SSD disolder mati sehingga tidak dapat di-upgrade mandiri"
      ],
      summary: "Laptop terbaik nomor 1 untuk mahasiswa, penulis, manajer, dan programmer yang mobile setiap hari."
    },
    warranty: {
      duration_months: 12,
      coverage: "Garansi Resmi Apple 1 Tahun Internasional & Indonesia, dapat diperpanjang via AppleCare+",
      claim_ease: 9,
      official_service_centers: 45,
      score: 88.0
    },
    marketplace_links: {
      tokopedia: "https://www.tokopedia.com/search?q=macbook+air+m3",
      shopee: "https://shopee.co.id/search?keyword=macbook+air+m3",
      lazada: "https://www.lazada.co.id/catalog/?q=macbook+air+m3"
    },
    tags: ["ultrabook", "fanless", "apple-silicon", "premium", "student"],
    release_year: 2024,
    score_performance: 85,
    score_camera: 60,
    score_battery: 97,
    score_display: 90,
    score_build_quality: 95,
    score_value: 70,
    score_audio: 82,
    score_software: 92
  },
  {
    id: "lp-002",
    name: "ASUS ROG Zephyrus G14 (2024)",
    brand: "ASUS",
    category: "laptop",
    price: 28999000,
    image: "https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=600&auto=format&fit=crop&q=80",
    description: "Laptop gaming & kreasi konten paling elegan dengan layar ROG Nebula OLED 120Hz, Ryzen 9, dan kartu grafis RTX 4060.",
    specs: {
      display: "14\" 3K (2880x1800) OLED 120Hz 0.2ms, G-Sync, 100% DCI-P3",
      processor: "AMD Ryzen 9 8945HS (8 Cores, 16 Threads, AMD Ryzen AI)",
      ram: "16 GB / 32 GB LPDDR5X 6400MHz",
      storage: "1 TB PCIe 4.0 NVMe M.2 SSD",
      battery: "73 Wh (Pengisian Type-C PD 100W)",
      camera: "1080p FHD IR Camera dengan Windows Hello",
      os: "Windows 11 Home + Office Home & Student 2021 Asli",
      weight: "1.5 kg",
      connectivity: "Wi-Fi 6E, Bluetooth 5.3, HDMI 2.1, USB4 Type-C",
      screen_size: "14 inch",
      gpu: "NVIDIA GeForce RTX 4060 Laptop GPU 8GB GDDR6 (90W TGP)",
      resolution: "2880 x 1800 (3K OLED)",
      refresh_rate: "120Hz",
      build_material: "CNC Unibody Aluminium Alloy dengan Slash Lighting LED",
      special_features: "Layar OLED Kalibrasi Pantone, 6 Speaker Woofer Dual-force, ROG Intelligent Cooling"
    },
    review_sentiment: {
      overall_score: 4.5,
      total_reviews: 5340,
      pros: [
        "Layar OLED 3K 120Hz memiliki kontras hitam pekat dan akurasi warna mutlak",
        "Sasis aluminium CNC setebal 1.59cm dengan bobot cuma 1.5kg mudah dibawa ke cafe",
        "Kombinasi Ryzen 9 & RTX 4060 sanggup melibas game modern resolusi tinggi",
        "Kualitas speaker laptop Windows terbaik menyaingi MacBook Pro"
      ],
      cons: [
        "RAM disolder sehingga tidak bisa ditambah di masa depan",
        "Suhu permukaan sasis aluminium terasa hangat ketika bermain game berat",
        "Harga tergolong tinggi untuk kategori laptop gaming 14 inci"
      ],
      summary: "Pilihan utama gamer profesional dan video editor yang menginginkan laptop tipis bertenaga gahar."
    },
    warranty: {
      duration_months: 24,
      coverage: "Garansi Resmi ASUS Indonesia 2 Tahun Global + 1 Tahun ASUS Perfect Warranty (kerusakan akibat kelalaian ditanggung)",
      claim_ease: 8,
      official_service_centers: 180,
      score: 85.0
    },
    marketplace_links: {
      tokopedia: "https://www.tokopedia.com/search?q=asus+rog+zephyrus+g14+2024",
      shopee: "https://shopee.co.id/search?keyword=asus+rog+zephyrus+g14+2024",
      lazada: "https://www.lazada.co.id/catalog/?q=asus+rog+zephyrus+g14+2024"
    },
    tags: ["gaming", "oled", "ultraportable", "rtx-4060", "creator"],
    release_year: 2024,
    score_performance: 92,
    score_camera: 35,
    score_battery: 65,
    score_display: 96,
    score_build_quality: 90,
    score_value: 62,
    score_audio: 85,
    score_software: 75
  },
  {
    id: "lp-003",
    name: "Lenovo ThinkPad X1 Carbon Gen 11",
    brand: "Lenovo",
    category: "laptop",
    price: 24999000,
    image: "https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?w=600&auto=format&fit=crop&q=80",
    description: "Ikon laptop bisnis kelas enterprise dengan bobot seringan bulu 1.12kg, uji ketahanan militer MIL-STD 810H, dan keyboard nomor 1 di dunia.",
    specs: {
      display: "14\" 2.8K (2880x1800) OLED Antirefleksi 400nits 100% DCI-P3",
      processor: "Intel Core i7-1365U vPro (10 Cores, 12 Threads)",
      ram: "16 GB / 32 GB LPDDR5 6000MHz",
      storage: "1 TB PCIe NVMe Gen 4 Performance SSD",
      battery: "57 Wh (Rapid Charge 80% dalam 60 menit)",
      camera: "FHD 1080p + IR Mobile Web Camera dengan Privacy Shutter mekanik",
      os: "Windows 11 Pro 64-bit Resmi",
      weight: "1.12 kg",
      connectivity: "Wi-Fi 6E, Bluetooth 5.1, 2x Thunderbolt 4, 2x USB-A 3.2, HDMI 2.0b, Nano SIM",
      screen_size: "14 inch",
      resolution: "2880 x 1800",
      build_material: "Tutup Serat Karbon Anyam, Rangka Magnesium Campuran",
      special_features: "TrackPoint Merah Khas, Uji Ketangguhan 12 Standar Militer, ThinkShield Security"
    },
    review_sentiment: {
      overall_score: 4.6,
      total_reviews: 7120,
      pros: [
        "Sensasi mengetik keyboard ThinkPad tidak ada tandingannya, empuk dan presisi",
        "Sangat ringan di angka 1.12 kg, serasa tidak membawa laptop di dalam tas ransel",
        "Fitur keamanan enterprise lengkap: vPro, pembaca sidik jari, dan webcam shutter",
        "Dukungan port konektivitas lengkap tanpa perlu repot membawa dongle adapter"
      ],
      cons: [
        "Hanya menggunakan grafis terintegrasi Intel Iris Xe, tidak cocok untuk gaming 3D",
        "Kapasitas baterai tergerus lebih cepat jika memilih opsi panel layar OLED 2.8K",
        "Harga pembelian unit baru tergolong tinggi untuk anggaran personal"
      ],
      summary: "Laptop standar emas para eksekutif perusahaan, konsultan, dan insinyur piranti lunak."
    },
    warranty: {
      duration_months: 36,
      coverage: "Garansi Resmi Lenovo Indonesia 3 Tahun On-Site Premier Support (Teknisi datang ke kantor/rumah)",
      claim_ease: 9,
      official_service_centers: 200,
      score: 92.0
    },
    marketplace_links: {
      tokopedia: "https://www.tokopedia.com/search?q=thinkpad+x1+carbon+gen+11",
      shopee: "https://shopee.co.id/search?keyword=thinkpad+x1+carbon+gen+11",
      lazada: "https://www.lazada.co.id/catalog/?q=thinkpad+x1+carbon+gen+11"
    },
    tags: ["business", "ultrabook", "mil-std", "oled", "enterprise"],
    release_year: 2023,
    score_performance: 78,
    score_camera: 65,
    score_battery: 88,
    score_display: 92,
    score_build_quality: 97,
    score_value: 55,
    score_audio: 70,
    score_software: 90
  },
  {
    id: "lp-004",
    name: "Acer Aspire 5 (A515-58M)",
    brand: "Acer",
    category: "laptop",
    price: 8499000,
    image: "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=600&auto=format&fit=crop&q=80",
    description: "Laptop kerja dan belajar serba bisa dengan Intel Core i5 Generasi 13, RAM DDR5 terbaru, dan layar lega 15.6 inci Full HD.",
    specs: {
      display: "15.6\" IPS Full HD, 1920x1080 Acer ComfyView",
      processor: "Intel Core i5-1335U (10 Cores, 12 Threads)",
      ram: "16 GB LPDDR5 Dual-Channel",
      storage: "512 GB PCIe Gen4 NVMe SSD",
      battery: "50 Wh (Hingga 9 jam penggunaan)",
      camera: "1080p FHD Webcam dengan teknologi Acer TNR (Noise Reduction)",
      os: "Windows 11 Home + Microsoft Office Asli Seumur Hidup",
      weight: "1.7 kg",
      connectivity: "Wi-Fi 6E, Bluetooth 5.1, Thunderbolt 4 Type-C, 2x USB 3.2 Gen 1, HDMI 2.1",
      screen_size: "15.6 inch",
      resolution: "1920 x 1080 (FHD)",
      build_material: "Top Cover Aluminium Metal, Bodi Bawah Polikarbonat",
      special_features: "Fingerprint Scanner di Trackpad, Port Thunderbolt 4 Serbaguna, Desain Engsel Elevasi Ergonomis"
    },
    review_sentiment: {
      overall_score: 4.2,
      total_reviews: 11200,
      pros: [
        "Harga di kisaran 8 jutaan sudah mendapatkan RAM 16GB LPDDR5 dan SSD 512GB",
        "Layar luas 15.6 inci memudahkan multitasking dua jendela dokumen berdampingan",
        "Paket komplit sudah termasuk Windows 11 dan Microsoft Office resmi permanen",
        "Port Thunderbolt 4 memungkinkan sambungan ke monitor eksternal resolusi 4K"
      ],
      cons: [
        "Tingkat kecerahan layar sekitar 250 nits kurang nyaman dipakai di area terbuka outdoor",
        "Dimensi fisik 15.6 inci membutuhkan ransel laptop berukuran cukup besar",
        "Rangka bodi bawah masih berbahan plastik standar"
      ],
      summary: "Pilihan laptop paling rasional dan ramah kantong untuk mahasiswa serta staf administrasi kantor."
    },
    warranty: {
      duration_months: 12,
      coverage: "Garansi Resmi Acer Indonesia 1 Tahun Sparepart + 3 Tahun Biaya Service",
      claim_ease: 7,
      official_service_centers: 150,
      score: 70.0
    },
    marketplace_links: {
      tokopedia: "https://www.tokopedia.com/search?q=acer+aspire+5+a515",
      shopee: "https://shopee.co.id/search?keyword=acer+aspire+5+a515",
      lazada: "https://www.lazada.co.id/catalog/?q=acer+aspire+5+a515"
    },
    tags: ["budget", "student", "value", "ddr5", "office"],
    release_year: 2023,
    score_performance: 68,
    score_camera: 40,
    score_battery: 72,
    score_display: 65,
    score_build_quality: 55,
    score_value: 92,
    score_audio: 55,
    score_software: 72
  },
  {
    id: "lp-005",
    name: "Lenovo LOQ 15IRX9",
    brand: "Lenovo",
    category: "laptop",
    price: 13999000,
    image: "https://images.unsplash.com/photo-1593642632823-8f785ba67e45?w=600&auto=format&fit=crop&q=80",
    description: "Laptop gaming entry-level dengan DNA Legion, dipersenjatai Intel Core i5 HX series, kartu grafis RTX 4050 6GB, dan layar 144Hz 100% sRGB.",
    specs: {
      display: "15.6\" FHD (1920x1080) IPS 144Hz, 100% sRGB, G-Sync",
      processor: "Intel Core i5-13450HX (10 Cores, 16 Threads, Max Turbo 4.6GHz)",
      ram: "16 GB DDR5 4800MHz (Dua slot, dapat diupgrade hingga 32GB)",
      storage: "512 GB SSD M.2 2242 PCIe 4.0 (Tersedia 1 slot M.2 kosong)",
      battery: "60 Wh (Super Rapid Charge Pro)",
      camera: "HD 720p dengan E-Shutter tombol privasi",
      os: "Windows 11 Home + Office Home & Student 2021",
      weight: "2.38 kg",
      connectivity: "Wi-Fi 6, Bluetooth 5.2, RJ-45 LAN Gigabit, HDMI 2.1, USB-C 100W PD",
      screen_size: "15.6 inch",
      gpu: "NVIDIA GeForce RTX 4050 6GB GDDR6 (105W TGP MUX Switch)",
      resolution: "1920 x 1080 (FHD)",
      refresh_rate: "144Hz",
      build_material: "Polycarbonate-ABS dengan pendingin ganda knalpot belakang",
      special_features: "Lenovo AI Engine+ dengan chip LA1 AI, Keyboard Legion TrueStrike dengan white backlight"
    },
    review_sentiment: {
      overall_score: 4.2,
      total_reviews: 6800,
      pros: [
        "RTX 4050 105W dan prosesor kelas HX sanggup memainkan Cyberpunk & Valorant dengan frame tinggi",
        "Layar sudah 100% sRGB, warna akurat untuk editing video dan gambar",
        "RAM dan SSD mudah di-upgrade dengan dua slot ekspansi yang terbuka",
        "Keyboard Legion TrueStrike nyaman untuk gaming kompetitif"
      ],
      cons: [
        "Bobot total bersama adaptor charger 170W mendekati 3 kg di dalam tas",
        "Baterai bertahan sekitar 3 jam jika tidak terhubung ke listrik AC",
        "Kualitas webcam 720p standar di pencahayaan redup"
      ],
      summary: "Pilihan laptop gaming paling masuk akal di bawah 15 juta dengan performa stabil dan silsilah Legion."
    },
    warranty: {
      duration_months: 24,
      coverage: "Garansi Resmi Lenovo Indonesia 2 Tahun Premium Care + 2 Tahun Accidental Damage Protection (ADP)",
      claim_ease: 8,
      official_service_centers: 200,
      score: 85.0
    },
    marketplace_links: {
      tokopedia: "https://www.tokopedia.com/search?q=lenovo+loq+15irx9",
      shopee: "https://shopee.co.id/search?keyword=lenovo+loq+15irx9",
      lazada: "https://www.lazada.co.id/catalog/?q=lenovo+loq+15irx9"
    },
    tags: ["gaming", "budget", "rtx-4050", "144hz", "value"],
    release_year: 2024,
    score_performance: 80,
    score_camera: 30,
    score_battery: 55,
    score_display: 70,
    score_build_quality: 60,
    score_value: 88,
    score_audio: 55,
    score_software: 72
  },

  // ── TABLETS ──
  {
    id: "tb-001",
    name: "iPad Air M2 (2024)",
    brand: "Apple",
    category: "tablet",
    price: 10999000,
    image: "https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?w=600&auto=format&fit=crop&q=80",
    description: "Tablet serbaguna berkekuatan chip M2 dengan dukungan Apple Pencil Pro, layar Liquid Retina 11 inci, dan desain tipis memukau.",
    specs: {
      display: "11\" Liquid Retina IPS LED, 2360x1640 500nits P3 Wide Color",
      processor: "Apple M2 (8-core CPU, 9-core GPU)",
      ram: "8 GB Unified Memory",
      storage: "128 GB / 256 GB / 512 GB / 1 TB",
      battery: "28.93 Wh (Hingga 10 jam menjelajah web via Wi-Fi)",
      camera: "12MP Kamera Belakang Wide 4K + 12MP Kamera Depan Lanskap Ultra Wide Center Stage",
      os: "iPadOS 17 (Dukungan Stage Manager)",
      weight: "462g",
      connectivity: "Wi-Fi 6E, Bluetooth 5.3, USB-C 3.1 Gen 2",
      screen_size: "11 inch",
      resolution: "2360 x 1640",
      build_material: "Aluminium Unibody 100% Daur Ulang",
      special_features: "Dukungan Apple Pencil Pro dengan Barrel Roll & Haptic, Magic Keyboard, Touch ID di tombol atas"
    },
    review_sentiment: {
      overall_score: 4.5,
      total_reviews: 8400,
      pros: [
        "Performa chip M2 sangat kencang untuk ilustrasi Procreate dan edit video 4K",
        "Dukungan Apple Pencil Pro dengan sensor haptic dan gesture tekan baru",
        "Kamera depan kini diposisikan horizontal pas untuk zoom meeting kuliah",
        "Ekosistem aplikasi khusus tablet di App Store sangat matang dan beragam"
      ],
      cons: [
        "Layar masih menggunakan refresh rate 60Hz standar (bukan 120Hz ProMotion)",
        "Aksesoris Apple Pencil Pro dan Magic Keyboard dijual terpisah dengan harga tinggi",
        "Sistem multitasking iPadOS belum sebebas macOS desktop sejati"
      ],
      summary: "Tablet terbaik untuk mahasiswa, desainer grafis, dan kreator konten digital."
    },
    warranty: {
      duration_months: 12,
      coverage: "Garansi Resmi Apple 1 Tahun iBox/Digimap",
      claim_ease: 9,
      official_service_centers: 45,
      score: 88.0
    },
    marketplace_links: {
      tokopedia: "https://www.tokopedia.com/search?q=ipad+air+m2+2024",
      shopee: "https://shopee.co.id/search?keyword=ipad+air+m2+2024",
      lazada: "https://www.lazada.co.id/catalog/?q=ipad+air+m2+2024"
    },
    tags: ["tablet", "apple-pencil", "m2-chip", "creative", "student"],
    release_year: 2024,
    score_performance: 90,
    score_camera: 60,
    score_battery: 80,
    score_display: 85,
    score_build_quality: 92,
    score_value: 68,
    score_audio: 80,
    score_software: 92
  },
  {
    id: "tb-002",
    name: "Samsung Galaxy Tab S9 FE",
    brand: "Samsung",
    category: "tablet",
    price: 6499000,
    image: "https://images.unsplash.com/photo-1561154464-82e9adf32764?w=600&auto=format&fit=crop&q=80",
    description: "Tablet Android paling komplit di kelas menengah, sudah menyertakan S Pen di dalam kotak dan memiliki sertifikasi tahan air IP68.",
    specs: {
      display: "10.9\" IPS LCD 90Hz, 2304x1440 Vision Booster",
      processor: "Samsung Exynos 1380 (5nm)",
      ram: "6 GB / 8 GB",
      storage: "128 GB / 256 GB + Slot MicroSD hingga 1TB",
      battery: "8000 mAh (45W Fast Charging)",
      camera: "8MP Kamera Utama + 12MP Kamera Depan Ultra-Wide",
      os: "Android 14 (One UI 6 dengan Samsung DeX)",
      weight: "523g",
      connectivity: "Wi-Fi 6, Bluetooth 5.3, USB-C 2.0",
      screen_size: "10.9 inch",
      resolution: "2304 x 1440",
      water_resistance: "IP68 (Tablet dan S Pen tahan air dan debu)",
      build_material: "Bodi Aluminium Armor yang kokoh",
      special_features: "Stylus S Pen bawaan gratis tanpa baterai, Antarmuka PC Samsung DeX, Dual Speaker AKG"
    },
    review_sentiment: {
      overall_score: 4.2,
      total_reviews: 5600,
      pros: [
        "Stylus S Pen sudah disertakan langsung tanpa perlu beli tambahan senilai 1 jutaan",
        "Sertifikasi IP68 tahan air sangat aman dipakai belajar di meja makan atau cafe outdoor",
        "Mode Samsung DeX menyulap tampilan tablet menjadi antarmuka desktop mirip laptop",
        "Slot MicroSD memungkinkan penambahan ruang penyimpanan hingga 1TB dengan murah"
      ],
      cons: [
        "Layar menggunakan panel IPS LCD bukan Super AMOLED khas Samsung",
        "Chipset Exynos 1380 kurang bertenaga untuk bermain game 3D berat di grafis rata kanan",
        "Kepala charger 45W tidak disertakan di paket penjualan"
      ],
      summary: "Tablet Android paling ramah kantong untuk mencatat kuliah, menggambar santai, dan menonton film."
    },
    warranty: {
      duration_months: 12,
      coverage: "Garansi Resmi SEIN Indonesia 1 Tahun",
      claim_ease: 8,
      official_service_centers: 350,
      score: 82.0
    },
    marketplace_links: {
      tokopedia: "https://www.tokopedia.com/search?q=samsung+galaxy+tab+s9+fe",
      shopee: "https://shopee.co.id/search?keyword=samsung+galaxy+tab+s9+fe",
      lazada: "https://www.lazada.co.id/catalog/?q=samsung+galaxy+tab+s9+fe"
    },
    tags: ["tablet", "s-pen", "ip68", "value", "student"],
    release_year: 2023,
    score_performance: 65,
    score_camera: 45,
    score_battery: 90,
    score_display: 72,
    score_build_quality: 78,
    score_value: 85,
    score_audio: 65,
    score_software: 80
  },

  // ── TWS / AUDIO ──
  {
    id: "tw-001",
    name: "Apple AirPods Pro 2 (USB-C)",
    brand: "Apple",
    category: "tws",
    price: 3799000,
    image: "https://images.unsplash.com/photo-1600294037681-c80b4cb5b434?w=600&auto=format&fit=crop&q=80",
    description: "TWS kelas rujukan dengan Active Noise Cancellation 2x lebih senyap, mode Transparansi Adaptif, dan charging case USB-C MagSafe.",
    specs: {
      display: "N/A",
      battery: "6 jam pemakaian (ANC On) / Total 30 jam bersama Casing MagSafe",
      connectivity: "Bluetooth 5.3, Chip Apple H2 di earbud, Chip Apple U1 di casing",
      weight: "5.3g per earbud / Casing 50.8g",
      water_resistance: "IP54 (Tahan debu, keringat, dan cipratan air untuk earbud dan casing)",
      driver_size: "Driver Kustom Apple High-Excursion dengan Amplifier Rentang Dinamis Tinggi",
      anc: "Active Noise Cancellation Generasi 2 dengan Adaptive Audio & Conversation Awareness",
      codec: "AAC, SBC, Apple Spatial Audio dengan Dynamic Head Tracking",
      build_material: "Polikarbonat Putih Glossy, Eartips Silikon 4 Ukuran (XS, S, M, L)",
      special_features: "Speaker di Casing untuk Find My, Kontrol Sentuh Volume Swipe, Pengisian MagSafe/Apple Watch Charger"
    },
    review_sentiment: {
      overall_score: 4.7,
      total_reviews: 22300,
      pros: [
        "Peredam bising aktif (ANC) paling efektif meredam bising mesin pesawat dan kendaraan umum",
        "Mode Transparansi sangat natural terdengar seperti tidak memakai earphone sama sekali",
        "Fitur Percakapan Cerdas otomatis mengecilkan volume musik saat kita mulai berbicara",
        "Casing kini berport universal USB-C dan memiliki speaker pelacak jika terselip"
      ],
      cons: [
        "Fitur-fitur terbaiknya terkunci eksklusif jika dipasangkan dengan ponsel Android",
        "Harganya lumayan menguras kantong untuk sepasang earphone nirkabel",
        "Karakter suara seimbang flat, kurang cocok bagi penikmat dentuman bass berlebihan"
      ],
      summary: "TWS wajib bagi para komuter dan pengguna setia produk Apple."
    },
    warranty: {
      duration_months: 12,
      coverage: "Garansi Resmi Apple Indonesia 1 Tahun (iBox/Digimap)",
      claim_ease: 9,
      official_service_centers: 45,
      score: 88.0
    },
    marketplace_links: {
      tokopedia: "https://www.tokopedia.com/search?q=airpods+pro+2+usb-c",
      shopee: "https://shopee.co.id/search?keyword=airpods+pro+2+usb-c",
      lazada: "https://www.lazada.co.id/catalog/?q=airpods+pro+2+usb-c"
    },
    tags: ["tws", "anc", "apple", "premium", "spatial-audio"],
    release_year: 2023,
    score_performance: 70,
    score_camera: 0,
    score_battery: 82,
    score_display: 0,
    score_build_quality: 88,
    score_value: 65,
    score_audio: 95,
    score_software: 92
  },
  {
    id: "tw-002",
    name: "Sony WF-1000XM5",
    brand: "Sony",
    category: "tws",
    price: 4299000,
    image: "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=600&auto=format&fit=crop&q=80",
    description: "Mahakarya audio nirkabel Sony dengan chip Integrated Processor V2, driver Dynamic Driver X 8.4mm, dan dukungan codec Hi-Res LDAC.",
    specs: {
      display: "N/A",
      battery: "8 jam (ANC On) / Total 24 jam dengan Casing, Cas Cepat 3 Menit untuk 60 Menit Main",
      connectivity: "Bluetooth 5.3, Dukungan Multipoint Connection 2 Perangkat Sekaligus",
      weight: "5.9g per earbud (25% lebih kecil dari XM4)",
      water_resistance: "IPX4 (Tahan percikan air dan keringat olahraga)",
      driver_size: "Dynamic Driver X 8.4mm Dirancang Khusus",
      anc: "Teknologi Multi-Noise Sensor dengan Prosesor V2 dan Chip QN2e",
      codec: "LDAC (Hi-Res Audio Wireless), LC3, AAC, SBC, DSEE Extreme AI Upscaling",
      build_material: "Bodi Finishing Glossy Elegan, Noise Isolation Earbud Tips Berbahan Polyurethane Foam",
      special_features: "Head Tracking 360 Reality Audio, Speak-to-Chat, Sensor Konduksi Tulang untuk Mikrofon Jernih"
    },
    review_sentiment: {
      overall_score: 4.6,
      total_reviews: 9800,
      pros: [
        "Kualitas suara resolusi tinggi terbaik berkat transmisi bit-rate tinggi LDAC",
        "Eartips busa polyurethane mengisolasi suara pasif dengan sangat kedap",
        "Bisa terhubung ke laptop dan smartphone secara bersamaan tanpa putus sambung",
        "Aplikasi Sony Headphones Connect menyediakan equalizer manual 10-band terlengkap"
      ],
      cons: [
        "Harga tertinggi di pasaran TWS komersial saat ini",
        "Eartips berbahan busa memerlukan perawatan ekstra dan lebih cepat aus dibanding silikon biasa",
        "Finishing bodi samping glossy sedikit licin saat diambil dari dalam wadah casing"
      ],
      summary: "Pilihan mutlak bagi kaum audiophile dan penikmat musik berkualitas tinggi di manapun berada."
    },
    warranty: {
      duration_months: 12,
      coverage: "Garansi Resmi Sony Indonesia 1 Tahun",
      claim_ease: 7,
      official_service_centers: 80,
      score: 75.0
    },
    marketplace_links: {
      tokopedia: "https://www.tokopedia.com/search?q=sony+wf-1000xm5",
      shopee: "https://shopee.co.id/search?keyword=sony+wf-1000xm5",
      lazada: "https://www.lazada.co.id/catalog/?q=sony+wf-1000xm5"
    },
    tags: ["tws", "anc", "hi-res", "ldac", "audiophile"],
    release_year: 2023,
    score_performance: 70,
    score_camera: 0,
    score_battery: 88,
    score_display: 0,
    score_build_quality: 85,
    score_value: 60,
    score_audio: 98,
    score_software: 82
  },
  {
    id: "tw-003",
    name: "Samsung Galaxy Buds3 Pro",
    brand: "Samsung",
    category: "tws",
    price: 3299000,
    image: "https://images.unsplash.com/photo-1546435770-a3e426bf472b?w=600&auto=format&fit=crop&q=80",
    description: "Evolusi TWS Samsung dengan desain blade aerodinamis, lampu Blade Lights futuristik, speaker 2-arah terpisah, dan penerjemah Galaxy AI.",
    specs: {
      display: "N/A",
      battery: "6 jam (ANC On) / Total 26 jam bersama wadah baterai",
      connectivity: "Bluetooth 5.4 dengan Auto Switch antar ekosistem Samsung",
      weight: "5.4g per earbud",
      water_resistance: "IP57 (Tahan debu dan celupan air hingga 1 meter)",
      driver_size: "Sistem Speaker Ganda: 10.5mm Dynamic Driver + 6.1mm Planar Tweeter",
      anc: "Adaptive ANC yang mendeteksi suara sirene dan alarm otomatis",
      codec: "Samsung Seamless Codec (SSC HiFi 24-bit/96kHz), AAC, SBC",
      build_material: "Rancangan Tangkai Segitiga (Blade Design) dengan Strip LED",
      special_features: "Live Interpreter Galaxy AI langsung ke telinga, 360 Audio dengan perekaman suara 3D, Kontrol Cubit dan Usap"
    },
    review_sentiment: {
      overall_score: 4.3,
      total_reviews: 4500,
      pros: [
        "Sistem speaker 2-arah menghasilkan nada tinggi kristal dan bass terpisah yang rapi",
        "Ketahanan air dan debu IP57 tertinggi di kelas earbud premium",
        "Fitur penerjemah percakapan instan Galaxy AI sangat praktis untuk liburan ke luar negeri",
        "Mikrofon berbasis machine-learning meredam suara angin saat berbicara di jalan"
      ],
      cons: [
        "Audio HiFi 24-bit 96kHz hanya aktif jika dipasangkan dengan ponsel flagship Samsung",
        "Desain tangkai baru menyerupai AirPods sehingga kehilangan identitas bentuk kacang sebelumnya",
        "Lampu strip LED menghabiskan daya baterai ekstra jika dibiarkan menyala terus"
      ],
      summary: "TWS canggih pelengkap sempurna bagi pemilik smartphone Samsung Galaxy."
    },
    warranty: {
      duration_months: 12,
      coverage: "Garansi Resmi SEIN Indonesia 1 Tahun",
      claim_ease: 8,
      official_service_centers: 350,
      score: 82.0
    },
    marketplace_links: {
      tokopedia: "https://www.tokopedia.com/search?q=samsung+galaxy+buds3+pro",
      shopee: "https://shopee.co.id/search?keyword=samsung+galaxy+buds3+pro",
      lazada: "https://www.lazada.co.id/catalog/?q=samsung+galaxy+buds3+pro"
    },
    tags: ["tws", "anc", "galaxy-ai", "blade-design", "2-way-speaker"],
    release_year: 2024,
    score_performance: 70,
    score_camera: 0,
    score_battery: 85,
    score_display: 0,
    score_build_quality: 80,
    score_value: 72,
    score_audio: 90,
    score_software: 85
  },
  {
    id: "tw-004",
    name: "QCY MeloBuds ANC (HT05)",
    brand: "QCY",
    category: "tws",
    price: 349000,
    image: "https://images.unsplash.com/photo-1572536147248-ac59a8abfa4b?w=600&auto=format&fit=crop&q=80",
    description: "Juara peredam bising harga merakyat dengan teknologi Hybrid ANC -40dB, 6 mikrofon ENC, dan baterai awet 30 jam di bawah 400 ribu rupiah.",
    specs: {
      display: "N/A",
      battery: "7.5 jam pemakaian / Total 30 jam bersama Casing pengisi daya",
      connectivity: "Bluetooth 5.2 dengan Low Latency Game Mode 68ms",
      weight: "4.7g per earbud",
      water_resistance: "IPX5 (Tahan keringat dan rintik hujan gerimis)",
      driver_size: "10mm Dynamic Driver Bio-Diaphragm LCP",
      anc: "Hybrid Active Noise Cancellation hingga kedalaman 40dB dengan 3 mode (Indoor, Commuting, Boosted)",
      codec: "AAC, SBC",
      build_material: "Bodi Polikarbonat Ringan Matte",
      special_features: "Aplikasi Pendukung QCY App untuk kustomisasi kontrol sentuh dan equalizer grafis, 6 Mikrofon ENC Noise Reduction"
    },
    review_sentiment: {
      overall_score: 4.1,
      total_reviews: 15600,
      pros: [
        "Harganya super terjangkau di kisaran 300 ribuan namun sudah memiliki ANC aktif yang benar-benar terasa",
        "Aplikasi ponselnya menyediakan pengaturan tombol dan profil equalizer yang lengkap",
        "Baterai sangat awet sanggup bertahan beberapa hari untuk pemakaian santai",
        "Bentuk earbud pas dan nyaman dipakai berlama-lama tanpa membuat telinga pegal"
      ],
      cons: [
        "Material plastik casing terasa ringan dan tipis khas barang ekonomis",
        "Kualitas tangkapan mikrofon kurang maksimal jika berada di tengah hembusan angin kencang",
        "Tidak memiliki sensor auto-pause ketika earbud dilepas dari telinga"
      ],
      summary: "TWS murah meriah terbaik untuk pelajar yang ingin fokus belajar tanpa terganggu suara bising sekitar."
    },
    warranty: {
      duration_months: 6,
      coverage: "Garansi Distributor Resmi QCY Indonesia 6 Bulan Ganti Baru",
      claim_ease: 4,
      official_service_centers: 20,
      score: 40.0
    },
    marketplace_links: {
      tokopedia: "https://www.tokopedia.com/search?q=qcy+melobuds+anc",
      shopee: "https://shopee.co.id/search?keyword=qcy+melobuds+anc",
      lazada: "https://www.lazada.co.id/catalog/?q=qcy+melobuds+anc"
    },
    tags: ["tws", "budget", "anc", "value", "affordable"],
    release_year: 2024,
    score_performance: 45,
    score_camera: 0,
    score_battery: 85,
    score_display: 0,
    score_build_quality: 40,
    score_value: 97,
    score_audio: 62,
    score_software: 50
  },

  // ── SMARTWATCHES ──
  {
    id: "sw-001",
    name: "Apple Watch Ultra 2",
    brand: "Apple",
    category: "smartwatch",
    price: 13999000,
    image: "https://images.unsplash.com/photo-1508685096489-7aacd43bd3b1?w=600&auto=format&fit=crop&q=80",
    description: "Jam tangan pintar petualangan paling tangguh dengan bodi titanium 49mm, layar 3000 nits, GPS frekuensi ganda presisi tinggi, dan ketahanan menyelam 40 meter.",
    specs: {
      display: "1.92\" Always-On Retina LTPO OLED, Kecerahan 3000 nits, Kaca Kristal Safir Datar",
      processor: "Apple S9 SiP 64-bit Dual-core dengan Neural Engine 4-core",
      battery: "Hingga 36 jam pemakaian normal / Hingga 72 jam dalam Mode Hemat Daya",
      connectivity: "Konektivitas Seluler LTE 4G Bawaan, Wi-Fi, Bluetooth 5.3, UWB Generasi 2",
      weight: "61.4g (Tanpa tali)",
      water_resistance: "100 meter (Sertifikasi Selam Rekreasi EN13319 hingga 40m, Standar Militer MIL-STD 810H)",
      screen_size: "49mm",
      resolution: "502 x 410",
      build_material: "Bodi Titanium Aerospace Grade 95% Daur Ulang dengan Tombol Action Kustom Berwarna Oranye",
      sensors: "Sensor Kedalaman Air, Pengukur Suhu Air, Sensor Suhu Tubuh, EKG Jantung, Oksigen Darah (SpO2), Kompas Presisi",
      special_features: "Sirene Darurat 86 Desibel terdengar hingga 180m, Gestur Sentuhan Ganda (Double Tap), Komputer Selam Oceanic+"
    },
    review_sentiment: {
      overall_score: 4.7,
      total_reviews: 6800,
      pros: [
        "Layar 3000 nits sangat jelas terbaca di bawah terik sinar matahari pantai dan gunung",
        "Konstruksi bodi titanium dengan tepi pelindung safir luar biasa tahan banting",
        "GPS frekuensi ganda L1 dan L5 paling akurat untuk navigasi lari maraton dan trail run",
        "Baterai bertahan 2 sampai 3 hari, jauh lebih awet dibandingkan Apple Watch seri standar"
      ],
      cons: [
        "Ukuran bodi 49mm cukup besar dan tebal untuk pergelangan tangan berukuran kecil",
        "Harga sebanding dengan satu unit laptop premium",
        "Tidak dapat disinkronkan sama sekali dengan smartphone non-iPhone"
      ],
      summary: "Smartwatch petualangan kelas atas untuk pelari maraton, penyelam laut, pendaki gunung, dan pencinta ekspedisi alam liar."
    },
    warranty: {
      duration_months: 12,
      coverage: "Garansi Resmi Apple 1 Tahun (iBox/Digimap), Perlindungan Global",
      claim_ease: 9,
      official_service_centers: 45,
      score: 88.0
    },
    marketplace_links: {
      tokopedia: "https://www.tokopedia.com/search?q=apple+watch+ultra+2",
      shopee: "https://shopee.co.id/search?keyword=apple+watch+ultra+2",
      lazada: "https://www.lazada.co.id/catalog/?q=apple+watch+ultra+2"
    },
    tags: ["smartwatch", "adventure", "titanium", "diving", "premium"],
    release_year: 2023,
    score_performance: 90,
    score_camera: 0,
    score_battery: 85,
    score_display: 95,
    score_build_quality: 98,
    score_value: 50,
    score_audio: 75,
    score_software: 92
  },
  {
    id: "sw-002",
    name: "Samsung Galaxy Watch 7",
    brand: "Samsung",
    category: "smartwatch",
    price: 4499000,
    image: "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600&auto=format&fit=crop&q=80",
    description: "Jam tangan pintar Android generasi baru dengan prosesor 3nm pertama di dunia, sensor kesehatan BioActive 13 LED, dan analisis kebugaran Galaxy AI.",
    specs: {
      display: "1.3\" Super AMOLED Always-On Display 2000 nits, Kaca Kristal Safir",
      processor: "Exynos W1000 (Penta-core 3nm Super Irit Daya)",
      battery: "Hingga 40 jam pemakaian normal (Fast Wireless Charging WPC)",
      connectivity: "GPS Dual-Frequency (L1+L5), Wi-Fi, Bluetooth 5.3, NFC Samsung Pay",
      weight: "28.8g (Ukuran 40mm) / 33.8g (Ukuran 44mm)",
      water_resistance: "5ATM + IP68 + Standar Militer MIL-STD-810H",
      screen_size: "40mm / 44mm",
      resolution: "432 x 432",
      build_material: "Rangka Armor Aluminium yang ringan dan elegan",
      sensors: "Samsung BioActive Sensor Generasi Terbaru (Detak Jantung Optik, Sinyal Jantung Elektrik EKG, Analisis Komposisi Tubuh BIA, Indeks AGEs)",
      special_features: "Energy Score harian bertenaga AI, Deteksi Sleep Apnea Medis Resmi, Balas Pesan Cerdas AI, Wear OS Powered by Samsung"
    },
    review_sentiment: {
      overall_score: 4.3,
      total_reviews: 7200,
      pros: [
        "Prosesor 3nm baru membuat navigasi antarmuka geser sangat responsif dan bebas lag",
        "Sensor kesehatan lengkap dapat mengukur kadar lemak tubuh, otot, hingga indeks penuaan metabolik",
        "GPS frekuensi ganda merekam rute lari perkotaan dengan akurasi lintasan tinggi",
        "Desain jam melingkar klasik sangat cocok dipakai untuk pertemuan formal maupun olahraga"
      ],
      cons: [
        "Masa pakai baterai rata-rata berkisar 1.5 hari sehingga perlu rutin dicas setiap hari",
        "Fitur EKG dan pengukur tekanan darah memerlukan smartphone Samsung Galaxy",
        "Waktu pengisian baterai membutuhkan sekitar 1 jam 15 menit"
      ],
      summary: "Smartwatch kesehatan terbaik bagi pengguna ponsel Android yang ingin memantau kebugaran secara mendalam."
    },
    warranty: {
      duration_months: 12,
      coverage: "Garansi Resmi SEIN Indonesia 1 Tahun",
      claim_ease: 8,
      official_service_centers: 350,
      score: 82.0
    },
    marketplace_links: {
      tokopedia: "https://www.tokopedia.com/search?q=samsung+galaxy+watch+7",
      shopee: "https://shopee.co.id/search?keyword=samsung+galaxy+watch+7",
      lazada: "https://www.lazada.co.id/catalog/?q=samsung+galaxy+watch+7"
    },
    tags: ["smartwatch", "wear-os", "galaxy-ai", "health", "3nm"],
    release_year: 2024,
    score_performance: 82,
    score_camera: 0,
    score_battery: 70,
    score_display: 88,
    score_build_quality: 82,
    score_value: 78,
    score_audio: 60,
    score_software: 85
  },
  {
    id: "sw-003",
    name: "Amazfit GTR 4",
    brand: "Amazfit",
    category: "smartwatch",
    price: 2999000,
    image: "https://images.unsplash.com/photo-1510017803434-a899398421b3?w=600&auto=format&fit=crop&q=80",
    description: "Juara daya tahan baterai hingga 14 hari penuh dengan bodi paduan aluminium klasik, layar HD AMOLED 1.43 inci, dan antena GPS sirkular polarisasi ganda.",
    specs: {
      display: "1.43\" Ultra HD AMOLED 466x466 326 ppi, Kaca Anti-Glare dengan Bezel Keramik",
      processor: "Chipset Khusus Hemat Energi Zepp OS 2.0",
      battery: "475 mAh (Hingga 14 hari pemakaian standar / 24 hari mode hemat)",
      connectivity: "Antena GPS Dual-band Polarisasi Sirkular, Wi-Fi 2.4GHz, Bluetooth 5.0 BLE",
      weight: "34g (Tanpa tali jam)",
      water_resistance: "5 ATM (Tahan tekanan air setara kedalaman 50 meter)",
      screen_size: "46mm",
      resolution: "466 x 466",
      build_material: "Bingkai Paduan Aluminium Kelas Penerbangan, Tombol Putar Mahkota Navigasi",
      sensors: "Sensor Biometrik BioTracker 4.0 PPG 2LED (Detak Jantung 24 Jam, SpO2, Tingkat Stres, Kualitas Tidur), Barometer Altimeter",
      special_features: "Penyimpanan Musik Offline Bawaan, Panggilan Telepon Bluetooth via Speaker & Mikrofon, 150+ Mode Olahraga dengan Pengenalan Latihan Kekuatan Otomatis"
    },
    review_sentiment: {
      overall_score: 4.3,
      total_reviews: 8900,
      pros: [
        "Baterai luar biasa awet tembus 2 minggu pemakaian tanpa perlu repot bawa charger saat traveling",
        "Kompatibel 100% dengan smartphone Android maupun iPhone iOS tanpa diskriminasi fitur",
        "Layar AMOLED jernih dengan ratusan pilihan tampilan muka jam gratis",
        "Bisa menerima dan melakukan panggilan telepon langsung dari pergelangan tangan"
      ],
      cons: [
        "Ekosistem aplikasi pihak ketiga Zepp OS masih terbatas dibanding Apple watchOS atau Google Wear OS",
        "Balasan notifikasi pesan WhatsApp hanya mendukung templat teks cepat yang sudah ditentukan sebelumnya",
        "Sensor NFC belum mendukung pembayaran digital nirsentuh di Indonesia"
      ],
      summary: "Smartwatch paling fungsional dan awet baterai untuk pengguna yang tidak mau repot mengecas jam setiap malam."
    },
    warranty: {
      duration_months: 12,
      coverage: "Garansi Resmi Amazfit Indonesia 1 Tahun Ganti Unit",
      claim_ease: 6,
      official_service_centers: 50,
      score: 62.0
    },
    marketplace_links: {
      tokopedia: "https://www.tokopedia.com/search?q=amazfit+gtr+4",
      shopee: "https://shopee.co.id/search?keyword=amazfit+gtr+4",
      lazada: "https://www.lazada.co.id/catalog/?q=amazfit+gtr+4"
    },
    tags: ["smartwatch", "amoled", "14-day-battery", "gps", "value"],
    release_year: 2023,
    score_performance: 65,
    score_camera: 0,
    score_battery: 95,
    score_display: 82,
    score_build_quality: 72,
    score_value: 90,
    score_audio: 40,
    score_software: 60
  }
];

export const CATEGORIES = [
  { id: "smartphone", label: "Smartphone", icon: "Smartphone", desc: "Flagship, Mid-Range, & Budget Gaming" },
  { id: "laptop", label: "Laptop", icon: "Laptop", desc: "Ultrabook, Workstation, & Gaming Beast" },
  { id: "tablet", label: "Tablet", icon: "Tablet", desc: "Produktivitas, Catatan, & Desain Kreatif" },
  { id: "tws", label: "TWS / Audio", icon: "Headphones", desc: "Peredam Bising (ANC) & Suara Hi-Res" },
  { id: "smartwatch", label: "Smartwatch", icon: "Watch", desc: "Pantau Kesehatan, Kebugaran, & Petualangan" },
];

export const SCENARIOS = [
  { id: "gaming", label: "Gaming Berat", desc: "Performa GPU tinggi & refresh rate mulus" },
  { id: "productivity", label: "Kerja & Produktivitas", desc: "Multitasking, keyboard nyaman, baterai tahan lama" },
  { id: "photography", label: "Fotografi & Kamera", desc: "Sensor lensa jernih, zoom optik, & akurasi warna" },
  { id: "content_creation", label: "Kreasi Konten / Video", desc: "Render cepat, layar akurat warna, & audio jernih" },
  { id: "business", label: "Bisnis & Mobilitas", desc: "Ringan, bodi tangguh, & keamanan data enterprise" },
  { id: "student", label: "Kuliah & Pelajar", desc: "Value terbaik, hemat anggaran, & awet bertahun-tahun" },
  { id: "fitness", label: "Olahraga & Outdoor", desc: "Tahan air IP68, sensor komprehensif, & GPS presisi" },
  { id: "multimedia", label: "Nonton & Hiburan", desc: "Layar cerah kontras tinggi & audio speaker mantap" },
  { id: "casual", label: "Penggunaan Sehari-hari", desc: "Baterai awet, navigasi sosial media lancar" },
];

export const TRADE_OFF_FACTORS = [
  { id: "performance", label: "Performa & Kecepatan", desc: "Kecepatan chipset, RAM, dan kemampuan beban berat" },
  { id: "camera", label: "Kualitas Kamera / Sensor", desc: "Detail gambar, zoom malam, dan rekaman video" },
  { id: "battery", label: "Ketahanan Baterai", desc: "Masa pakai berjam-jam tanpa perlu sering colok charger" },
  { id: "display", label: "Kejernihan Layar", desc: "Resolusi tinggi, panel AMOLED/OLED, dan 120Hz" },
  { id: "build_quality", label: "Durabilitas & Material", desc: "Bodi logam/titanium, ketahanan air, dan desain premium" },
  { id: "value", label: "Nilai Tukar Uang (Value)", desc: "Mendapatkan fitur semaksimal mungkin di harga serendah mungkin" },
];
