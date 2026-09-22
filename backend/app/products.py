"""
CompareBuy — Curated Product Database
~20 products across 5 categories with realistic Indonesian market data.
"""
from app.models import (
    Product, ProductSpecs, ReviewSentiment, WarrantyInfo, ProductCategory
)

PRODUCTS: list[Product] = [
    # ═══════════════════════════════════════════
    # SMARTPHONES
    # ═══════════════════════════════════════════
    Product(
        id="sm-001",
        name="Samsung Galaxy S24 Ultra",
        brand="Samsung",
        category=ProductCategory.SMARTPHONE,
        price=19999000,
        image="/images/samsung-s24-ultra.webp",
        description="Flagship Samsung dengan S Pen, kamera 200MP, dan layar Dynamic AMOLED 2X terbaik di kelasnya.",
        specs=ProductSpecs(
            display="6.8\" Dynamic AMOLED 2X, 3120x1440",
            processor="Snapdragon 8 Gen 3",
            ram="12 GB",
            storage="256 GB / 512 GB / 1 TB",
            battery="5000 mAh",
            camera="200MP + 50MP + 12MP + 10MP",
            os="Android 14 (One UI 6.1)",
            weight="232g",
            connectivity="5G, Wi-Fi 7, Bluetooth 5.3, UWB",
            refresh_rate="1-120Hz Adaptive",
            resolution="3120 x 1440 (QHD+)",
            water_resistance="IP68",
            build_material="Titanium Frame, Gorilla Armor",
            special_features="S Pen, Galaxy AI, Nightography"
        ),
        review_sentiment=ReviewSentiment(
            overall_score=4.6,
            total_reviews=12840,
            pros=["Kamera zoom 100x luar biasa", "S Pen sangat produktif", "Layar super tajam & terang", "Galaxy AI berguna di keseharian", "Baterai tahan seharian penuh"],
            cons=["Berat dan besar", "Harga sangat premium", "Pengisian daya relatif lambat (45W)"],
            summary="Smartphone Android terlengkap untuk power users yang butuh produktivitas dan kamera terbaik."
        ),
        warranty=WarrantyInfo(
            duration_months=12,
            coverage="Garansi resmi Samsung Indonesia — kerusakan hardware, bukan kerusakan fisik/air",
            claim_ease=8,
            official_service_centers=350,
            score=82.0
        ),
        marketplace_links={
            "tokopedia": "https://www.tokopedia.com/search?q=samsung+galaxy+s24+ultra",
            "shopee": "https://shopee.co.id/search?keyword=samsung+galaxy+s24+ultra",
            "lazada": "https://www.lazada.co.id/catalog/?q=samsung+galaxy+s24+ultra"
        },
        tags=["flagship", "s-pen", "200mp", "ai", "titanium", "5g"],
        release_year=2024,
        score_performance=95,
        score_camera=98,
        score_battery=80,
        score_display=97,
        score_build_quality=95,
        score_value=60,
        score_audio=82,
        score_software=88
    ),
    Product(
        id="sm-002",
        name="iPhone 15 Pro Max",
        brand="Apple",
        category=ProductCategory.SMARTPHONE,
        price=22499000,
        image="/images/iphone-15-pro-max.webp",
        description="iPhone termahal dengan chip A17 Pro, kamera periscope 5x, dan body titanium premium.",
        specs=ProductSpecs(
            display="6.7\" Super Retina XDR OLED, 2796x1290",
            processor="A17 Pro (3nm)",
            ram="8 GB",
            storage="256 GB / 512 GB / 1 TB",
            battery="4441 mAh",
            camera="48MP + 12MP + 12MP (Periscope 5x)",
            os="iOS 17",
            weight="221g",
            connectivity="5G, Wi-Fi 6E, Bluetooth 5.3, UWB",
            refresh_rate="1-120Hz ProMotion",
            resolution="2796 x 1290",
            water_resistance="IP68",
            build_material="Titanium Frame, Ceramic Shield",
            special_features="Action Button, USB-C, ProRes Video"
        ),
        review_sentiment=ReviewSentiment(
            overall_score=4.7,
            total_reviews=18920,
            pros=["Performa chip A17 Pro tak tertandingi", "Ekosistem Apple seamless", "Video recording terbaik di smartphone", "Build quality premium titanium", "Software update 5+ tahun"],
            cons=["Harga paling mahal", "Customization terbatas", "Charger dan aksesoris terpisah"],
            summary="Pilihan terbaik untuk pengguna ekosistem Apple yang butuh performa dan kamera video terbaik."
        ),
        warranty=WarrantyInfo(
            duration_months=12,
            coverage="Garansi resmi Apple — kerusakan hardware, bisa diperpanjang AppleCare+",
            claim_ease=9,
            official_service_centers=45,
            score=88.0
        ),
        marketplace_links={
            "tokopedia": "https://www.tokopedia.com/search?q=iphone+15+pro+max",
            "shopee": "https://shopee.co.id/search?keyword=iphone+15+pro+max",
            "lazada": "https://www.lazada.co.id/catalog/?q=iphone+15+pro+max"
        },
        tags=["flagship", "titanium", "a17-pro", "5g", "ios", "periscope"],
        release_year=2023,
        score_performance=97,
        score_camera=94,
        score_battery=78,
        score_display=95,
        score_build_quality=96,
        score_value=55,
        score_audio=85,
        score_software=95
    ),
    Product(
        id="sm-003",
        name="Google Pixel 8 Pro",
        brand="Google",
        category=ProductCategory.SMARTPHONE,
        price=14999000,
        image="/images/pixel-8-pro.webp",
        description="Smartphone AI-first dari Google dengan kamera komputasional terbaik dan 7 tahun update.",
        specs=ProductSpecs(
            display="6.7\" LTPO OLED, 2992x1344",
            processor="Google Tensor G3",
            ram="12 GB",
            storage="128 GB / 256 GB / 512 GB",
            battery="5050 mAh",
            camera="50MP + 48MP + 48MP",
            os="Android 14 (Stock)",
            weight="213g",
            connectivity="5G, Wi-Fi 7, Bluetooth 5.3",
            refresh_rate="1-120Hz LTPO",
            resolution="2992 x 1344",
            water_resistance="IP68",
            build_material="Aluminum Frame, Gorilla Glass Victus 2",
            special_features="Magic Eraser, Best Take, Audio Magic Eraser, 7yr updates"
        ),
        review_sentiment=ReviewSentiment(
            overall_score=4.4,
            total_reviews=6730,
            pros=["AI photo editing terbaik", "Stock Android paling bersih", "7 tahun update OS & security", "Night mode kamera luar biasa"],
            cons=["Tensor G3 kurang kencang untuk gaming", "Service center terbatas di Indonesia", "Kadang overheat saat multitask berat"],
            summary="Smartphone terbaik untuk pecinta fotografi komputasional dan pure Android experience."
        ),
        warranty=WarrantyInfo(
            duration_months=12,
            coverage="Garansi resmi Google — hardware, bisa diperpanjang via Google Store",
            claim_ease=5,
            official_service_centers=10,
            score=58.0
        ),
        marketplace_links={
            "tokopedia": "https://www.tokopedia.com/search?q=google+pixel+8+pro",
            "shopee": "https://shopee.co.id/search?keyword=google+pixel+8+pro",
            "lazada": "https://www.lazada.co.id/catalog/?q=google+pixel+8+pro"
        },
        tags=["ai-camera", "stock-android", "7yr-update", "5g", "flagship"],
        release_year=2023,
        score_performance=80,
        score_camera=96,
        score_battery=82,
        score_display=90,
        score_build_quality=82,
        score_value=75,
        score_audio=78,
        score_software=98
    ),
    Product(
        id="sm-004",
        name="Xiaomi 14 Ultra",
        brand="Xiaomi",
        category=ProductCategory.SMARTPHONE,
        price=14999000,
        image="/images/xiaomi-14-ultra.webp",
        description="Flagship Xiaomi kolaborasi Leica dengan kamera 1-inch sensor dan performa kelas atas.",
        specs=ProductSpecs(
            display="6.73\" LTPO AMOLED, 3200x1440",
            processor="Snapdragon 8 Gen 3",
            ram="16 GB",
            storage="512 GB",
            battery="5000 mAh",
            camera="50MP (1-inch Sony LYT-900) + 50MP + 50MP",
            os="Android 14 (HyperOS)",
            weight="227g",
            connectivity="5G, Wi-Fi 7, Bluetooth 5.4",
            refresh_rate="1-120Hz LTPO",
            resolution="3200 x 1440 (QHD+)",
            water_resistance="IP68",
            build_material="Aluminum Frame, Eco Leather / Glass",
            special_features="Leica Optics, 1-inch Sensor, Photography Kit Support"
        ),
        review_sentiment=ReviewSentiment(
            overall_score=4.5,
            total_reviews=4280,
            pros=["Sensor kamera 1-inch terbaik untuk low-light", "Leica color science natural", "RAM 16GB multitask mulus", "Layar QHD+ sangat tajam"],
            cons=["HyperOS masih ada bug sesekali", "Photography kit aksesoris mahal", "Agak berat untuk ukurannya"],
            summary="Smartphone fotografer profesional dengan sensor kamera terbesar dan kolaborasi Leica."
        ),
        warranty=WarrantyInfo(
            duration_months=12,
            coverage="Garansi resmi Xiaomi Indonesia — hardware",
            claim_ease=7,
            official_service_centers=280,
            score=74.0
        ),
        marketplace_links={
            "tokopedia": "https://www.tokopedia.com/search?q=xiaomi+14+ultra",
            "shopee": "https://shopee.co.id/search?keyword=xiaomi+14+ultra",
            "lazada": "https://www.lazada.co.id/catalog/?q=xiaomi+14+ultra"
        },
        tags=["leica", "1-inch-sensor", "flagship", "5g", "photography"],
        release_year=2024,
        score_performance=94,
        score_camera=97,
        score_battery=81,
        score_display=93,
        score_build_quality=88,
        score_value=72,
        score_audio=80,
        score_software=78
    ),
    Product(
        id="sm-005",
        name="POCO X6 Pro 5G",
        brand="POCO",
        category=ProductCategory.SMARTPHONE,
        price=3999000,
        image="/images/poco-x6-pro.webp",
        description="Mid-range killer dengan Dimensity 8300 Ultra, layar AMOLED 120Hz, dan pengisian daya 67W.",
        specs=ProductSpecs(
            display="6.67\" Flow AMOLED, 2712x1220",
            processor="MediaTek Dimensity 8300 Ultra",
            ram="8 GB / 12 GB",
            storage="256 GB / 512 GB",
            battery="5000 mAh",
            camera="64MP + 8MP + 2MP",
            os="Android 14 (HyperOS)",
            weight="186g",
            connectivity="5G, Wi-Fi 6, Bluetooth 5.3",
            refresh_rate="120Hz",
            resolution="2712 x 1220 (1.5K)",
            water_resistance="IP54",
            build_material="Plastic Frame, Gorilla Glass Victus",
            special_features="67W Turbo Charging, LiquidCool 2.0"
        ),
        review_sentiment=ReviewSentiment(
            overall_score=4.3,
            total_reviews=8950,
            pros=["Performa gaming luar biasa di harganya", "Layar AMOLED 1.5K sangat tajam", "Charging 67W super cepat", "Harga sangat kompetitif"],
            cons=["Kamera ultrawide biasa saja", "Build plastik kurang premium", "Bloatware cukup banyak"],
            summary="Best value smartphone untuk gaming dan penggunaan sehari-hari di bawah 5 juta."
        ),
        warranty=WarrantyInfo(
            duration_months=12,
            coverage="Garansi resmi POCO/Xiaomi Indonesia — hardware",
            claim_ease=7,
            official_service_centers=280,
            score=74.0
        ),
        marketplace_links={
            "tokopedia": "https://www.tokopedia.com/search?q=poco+x6+pro",
            "shopee": "https://shopee.co.id/search?keyword=poco+x6+pro",
            "lazada": "https://www.lazada.co.id/catalog/?q=poco+x6+pro"
        },
        tags=["mid-range", "gaming", "5g", "value", "fast-charging"],
        release_year=2024,
        score_performance=82,
        score_camera=65,
        score_battery=85,
        score_display=84,
        score_build_quality=62,
        score_value=95,
        score_audio=68,
        score_software=70
    ),

    # ═══════════════════════════════════════════
    # LAPTOPS
    # ═══════════════════════════════════════════
    Product(
        id="lp-001",
        name="MacBook Air M3",
        brand="Apple",
        category=ProductCategory.LAPTOP,
        price=18499000,
        image="/images/macbook-air-m3.webp",
        description="Laptop ultraportable Apple dengan chip M3, fanless design, dan baterai hingga 18 jam.",
        specs=ProductSpecs(
            display="13.6\" Liquid Retina, 2560x1664",
            processor="Apple M3 (8-core CPU, 10-core GPU)",
            ram="8 GB / 16 GB / 24 GB Unified",
            storage="256 GB / 512 GB / 1 TB / 2 TB SSD",
            battery="52.6 Wh (Up to 18 hours)",
            camera="1080p FaceTime HD",
            os="macOS Sonoma",
            weight="1.24 kg",
            connectivity="Wi-Fi 6E, Bluetooth 5.3",
            screen_size="13.6 inch",
            resolution="2560 x 1664",
            build_material="100% Recycled Aluminum",
            special_features="MagSafe, Fanless Design, Spatial Audio"
        ),
        review_sentiment=ReviewSentiment(
            overall_score=4.7,
            total_reviews=15200,
            pros=["Baterai tahan 18 jam nyata", "Fanless — zero noise", "Performa M3 sangat kencang untuk daily use", "Build quality premium aluminum", "Layar Liquid Retina tajam"],
            cons=["RAM 8GB base kurang untuk heavy multitask", "Port terbatas (2x USB-C)", "Tidak bisa upgrade RAM/Storage"],
            summary="Laptop terbaik untuk mahasiswa dan profesional yang butuh portabilitas dan baterai tahan lama."
        ),
        warranty=WarrantyInfo(
            duration_months=12,
            coverage="Garansi resmi Apple — kerusakan hardware, bisa diperpanjang AppleCare+",
            claim_ease=9,
            official_service_centers=45,
            score=88.0
        ),
        marketplace_links={
            "tokopedia": "https://www.tokopedia.com/search?q=macbook+air+m3",
            "shopee": "https://shopee.co.id/search?keyword=macbook+air+m3",
            "lazada": "https://www.lazada.co.id/catalog/?q=macbook+air+m3"
        },
        tags=["ultrabook", "fanless", "apple-silicon", "premium", "student"],
        release_year=2024,
        score_performance=85,
        score_camera=60,
        score_battery=97,
        score_display=90,
        score_build_quality=95,
        score_value=70,
        score_audio=82,
        score_software=92
    ),
    Product(
        id="lp-002",
        name="ASUS ROG Zephyrus G14 (2024)",
        brand="ASUS",
        category=ProductCategory.LAPTOP,
        price=28999000,
        image="/images/rog-zephyrus-g14.webp",
        description="Laptop gaming ultraportable dengan AMD Ryzen 9, RTX 4060, dan layar OLED 120Hz.",
        specs=ProductSpecs(
            display="14\" 2.8K OLED, 2880x1800",
            processor="AMD Ryzen 9 8945HS",
            ram="16 GB / 32 GB DDR5",
            storage="1 TB PCIe 4.0 SSD",
            battery="73 Wh",
            os="Windows 11 Home",
            weight="1.5 kg",
            connectivity="Wi-Fi 6E, Bluetooth 5.3",
            screen_size="14 inch",
            gpu="NVIDIA GeForce RTX 4060 8GB",
            resolution="2880 x 1800 (2.8K)",
            refresh_rate="120Hz OLED",
            build_material="Aluminum Alloy (CNC-milled)",
            special_features="AniMe Matrix LED, ROG Nebula OLED, 100W USB-C PD"
        ),
        review_sentiment=ReviewSentiment(
            overall_score=4.5,
            total_reviews=5340,
            pros=["OLED 2.8K 120Hz HDR luar biasa", "RTX 4060 cukup untuk AAA gaming", "Portabel hanya 1.5kg", "Build quality CNC aluminum premium", "AniMe Matrix unik"],
            cons=["Harga premium untuk 14 inch", "Baterai hanya 4-5 jam saat gaming", "Webcam 720p kurang tajam"],
            summary="Laptop gaming portabel terbaik dengan layar OLED dan performa yang kuat."
        ),
        warranty=WarrantyInfo(
            duration_months=24,
            coverage="Garansi resmi ASUS Indonesia — 2 tahun hardware, termasuk baterai",
            claim_ease=8,
            official_service_centers=180,
            score=85.0
        ),
        marketplace_links={
            "tokopedia": "https://www.tokopedia.com/search?q=asus+rog+zephyrus+g14+2024",
            "shopee": "https://shopee.co.id/search?keyword=asus+rog+zephyrus+g14+2024",
            "lazada": "https://www.lazada.co.id/catalog/?q=asus+rog+zephyrus+g14+2024"
        },
        tags=["gaming", "oled", "ultraportable", "rtx-4060", "creator"],
        release_year=2024,
        score_performance=92,
        score_camera=35,
        score_battery=65,
        score_display=96,
        score_build_quality=90,
        score_value=62,
        score_audio=85,
        score_software=75
    ),
    Product(
        id="lp-003",
        name="Lenovo ThinkPad X1 Carbon Gen 11",
        brand="Lenovo",
        category=ProductCategory.LAPTOP,
        price=24999000,
        image="/images/thinkpad-x1-carbon.webp",
        description="Laptop bisnis premium ultra-ringan dengan keyboard legendaris dan keamanan enterprise.",
        specs=ProductSpecs(
            display="14\" 2.8K OLED, 2880x1800",
            processor="Intel Core i7-1365U",
            ram="16 GB / 32 GB LPDDR5",
            storage="512 GB / 1 TB PCIe Gen4 SSD",
            battery="57 Wh (Up to 15 hours)",
            os="Windows 11 Pro",
            weight="1.12 kg",
            connectivity="Wi-Fi 6E, Bluetooth 5.3, 4G LTE Optional",
            screen_size="14 inch",
            resolution="2880 x 1800 (2.8K)",
            build_material="Carbon Fiber + Magnesium Alloy",
            special_features="MIL-STD-810H, Fingerprint + IR Camera, TrackPoint"
        ),
        review_sentiment=ReviewSentiment(
            overall_score=4.6,
            total_reviews=7120,
            pros=["Keyboard ThinkPad terbaik di industri", "Ultra-ringan 1.12kg", "Build MIL-STD tahan banting", "Layar OLED opsional gorgeous", "Fitur keamanan enterprise lengkap"],
            cons=["Harga sangat premium", "GPU integrated saja", "Speaker agak kecil"],
            summary="Laptop bisnis terbaik untuk profesional yang butuh durabilitas, keamanan, dan keyboard superior."
        ),
        warranty=WarrantyInfo(
            duration_months=36,
            coverage="Garansi resmi Lenovo — 3 tahun on-site service, Premier Support tersedia",
            claim_ease=9,
            official_service_centers=200,
            score=92.0
        ),
        marketplace_links={
            "tokopedia": "https://www.tokopedia.com/search?q=thinkpad+x1+carbon+gen+11",
            "shopee": "https://shopee.co.id/search?keyword=thinkpad+x1+carbon+gen+11",
            "lazada": "https://www.lazada.co.id/catalog/?q=thinkpad+x1+carbon+gen+11"
        },
        tags=["business", "ultrabook", "mil-std", "oled", "enterprise"],
        release_year=2023,
        score_performance=78,
        score_camera=65,
        score_battery=88,
        score_display=92,
        score_build_quality=97,
        score_value=55,
        score_audio=70,
        score_software=90
    ),
    Product(
        id="lp-004",
        name="Acer Aspire 5 (A515-58M)",
        brand="Acer",
        category=ProductCategory.LAPTOP,
        price=8499000,
        image="/images/acer-aspire-5.webp",
        description="Laptop value-for-money untuk mahasiswa dan pekerja dengan Intel Core i5 Gen 13 dan layar IPS Full HD.",
        specs=ProductSpecs(
            display="15.6\" IPS FHD, 1920x1080",
            processor="Intel Core i5-1335U",
            ram="8 GB / 16 GB DDR5",
            storage="512 GB PCIe SSD",
            battery="50 Wh (Up to 10 hours)",
            os="Windows 11 Home",
            weight="1.7 kg",
            connectivity="Wi-Fi 6, Bluetooth 5.1",
            screen_size="15.6 inch",
            resolution="1920 x 1080 (FHD)",
            build_material="Aluminum Lid, Plastic Body",
            special_features="Fingerprint Reader, USB-C PD Charging"
        ),
        review_sentiment=ReviewSentiment(
            overall_score=4.2,
            total_reviews=11200,
            pros=["Harga sangat terjangkau", "DDR5 di harga segini jarang", "SSD 512GB lega", "Layar IPS cukup baik", "Port lengkap"],
            cons=["Build plastik kurang premium", "Layar kurang terang outdoor", "RAM terpatri di beberapa varian"],
            summary="Best value laptop untuk mahasiswa dan pekerja kantoran yang butuh performa cukup di budget terbatas."
        ),
        warranty=WarrantyInfo(
            duration_months=12,
            coverage="Garansi resmi Acer Indonesia — 1 tahun hardware",
            claim_ease=7,
            official_service_centers=150,
            score=70.0
        ),
        marketplace_links={
            "tokopedia": "https://www.tokopedia.com/search?q=acer+aspire+5+a515",
            "shopee": "https://shopee.co.id/search?keyword=acer+aspire+5+a515",
            "lazada": "https://www.lazada.co.id/catalog/?q=acer+aspire+5+a515"
        },
        tags=["budget", "student", "value", "ddr5", "office"],
        release_year=2023,
        score_performance=68,
        score_camera=40,
        score_battery=72,
        score_display=65,
        score_build_quality=55,
        score_value=92,
        score_audio=55,
        score_software=72
    ),

    # ═══════════════════════════════════════════
    # TABLETS
    # ═══════════════════════════════════════════
    Product(
        id="tb-001",
        name="iPad Air M2 (2024)",
        brand="Apple",
        category=ProductCategory.TABLET,
        price=10999000,
        image="/images/ipad-air-m2.webp",
        description="Tablet premium Apple dengan chip M2, layar Liquid Retina 11\", dan dukungan Apple Pencil Pro.",
        specs=ProductSpecs(
            display="11\" Liquid Retina IPS, 2360x1640",
            processor="Apple M2",
            ram="8 GB",
            storage="128 GB / 256 GB / 512 GB / 1 TB",
            battery="28.93 Wh (Up to 10 hours)",
            camera="12MP Wide",
            os="iPadOS 17",
            weight="462g",
            connectivity="Wi-Fi 6E, Bluetooth 5.3, Optional 5G",
            screen_size="11 inch",
            resolution="2360 x 1640",
            build_material="100% Recycled Aluminum",
            special_features="Apple Pencil Pro, Magic Keyboard, Stage Manager"
        ),
        review_sentiment=ReviewSentiment(
            overall_score=4.5,
            total_reviews=8400,
            pros=["Chip M2 super powerful", "Apple Pencil Pro untuk kreativitas", "Desain tipis dan ringan", "Ekosistem iPadOS matang"],
            cons=["Storage 128GB base sedikit", "Layar bukan OLED", "Magic Keyboard mahal terpisah"],
            summary="Tablet terbaik untuk kreativitas, catatan kuliah, dan produktivitas sehari-hari."
        ),
        warranty=WarrantyInfo(
            duration_months=12,
            coverage="Garansi resmi Apple — hardware, bisa diperpanjang AppleCare+",
            claim_ease=9,
            official_service_centers=45,
            score=88.0
        ),
        marketplace_links={
            "tokopedia": "https://www.tokopedia.com/search?q=ipad+air+m2+2024",
            "shopee": "https://shopee.co.id/search?keyword=ipad+air+m2+2024",
            "lazada": "https://www.lazada.co.id/catalog/?q=ipad+air+m2+2024"
        },
        tags=["tablet", "apple-pencil", "m2-chip", "creative", "student"],
        release_year=2024,
        score_performance=90,
        score_camera=60,
        score_battery=80,
        score_display=85,
        score_build_quality=92,
        score_value=68,
        score_audio=80,
        score_software=92
    ),
    Product(
        id="tb-002",
        name="Samsung Galaxy Tab S9 FE",
        brand="Samsung",
        category=ProductCategory.TABLET,
        price=6499000,
        image="/images/galaxy-tab-s9-fe.webp",
        description="Tablet Samsung mid-range dengan S Pen included, layar TFT 10.9\", dan IP68 water resistance.",
        specs=ProductSpecs(
            display="10.9\" TFT LCD, 2304x1440",
            processor="Exynos 1380",
            ram="6 GB / 8 GB",
            storage="128 GB / 256 GB + microSD",
            battery="8000 mAh",
            camera="8MP Rear + 12MP Front",
            os="Android 14 (One UI 6)",
            weight="523g",
            connectivity="Wi-Fi 6, Bluetooth 5.3",
            screen_size="10.9 inch",
            resolution="2304 x 1440",
            water_resistance="IP68",
            build_material="Aluminum Frame",
            special_features="S Pen Included, Samsung DeX, IP68"
        ),
        review_sentiment=ReviewSentiment(
            overall_score=4.2,
            total_reviews=5600,
            pros=["S Pen sudah termasuk", "IP68 tahan air", "Baterai 8000mAh tahan lama", "MicroSD expandable", "Harga terjangkau"],
            cons=["Layar TFT bukan AMOLED", "Prosesor Exynos kurang kencang", "Kamera biasa saja"],
            summary="Tablet mid-range terbaik dengan S Pen included dan durabilitas IP68."
        ),
        warranty=WarrantyInfo(
            duration_months=12,
            coverage="Garansi resmi Samsung Indonesia — hardware",
            claim_ease=8,
            official_service_centers=350,
            score=82.0
        ),
        marketplace_links={
            "tokopedia": "https://www.tokopedia.com/search?q=samsung+galaxy+tab+s9+fe",
            "shopee": "https://shopee.co.id/search?keyword=samsung+galaxy+tab+s9+fe",
            "lazada": "https://www.lazada.co.id/catalog/?q=samsung+galaxy+tab+s9+fe"
        },
        tags=["tablet", "s-pen", "ip68", "value", "student"],
        release_year=2023,
        score_performance=65,
        score_camera=45,
        score_battery=90,
        score_display=72,
        score_build_quality=78,
        score_value=85,
        score_audio=65,
        score_software=80
    ),

    # ═══════════════════════════════════════════
    # TWS / EARBUDS
    # ═══════════════════════════════════════════
    Product(
        id="tw-001",
        name="Apple AirPods Pro 2 (USB-C)",
        brand="Apple",
        category=ProductCategory.TWS,
        price=3799000,
        image="/images/airpods-pro-2.webp",
        description="TWS premium Apple dengan ANC terbaik di kelasnya, Adaptive Audio, dan USB-C.",
        specs=ProductSpecs(
            display="N/A",
            battery="6h (ANC On) + 30h (Case)",
            connectivity="Bluetooth 5.3",
            weight="5.3g per earbud",
            water_resistance="IP54",
            driver_size="Custom Apple H2 Driver",
            anc="Active Noise Cancellation + Adaptive Transparency",
            codec="AAC, Spatial Audio with Head Tracking",
            build_material="Silicone Tips, Plastic Body",
            special_features="Conversation Awareness, Personalized Volume, USB-C MagSafe Case"
        ),
        review_sentiment=ReviewSentiment(
            overall_score=4.7,
            total_reviews=22300,
            pros=["ANC terbaik di TWS manapun", "Adaptive Audio game-changer", "Spatial Audio immersive", "USB-C universal", "Integrasi Apple sempurna"],
            cons=["Mahal untuk TWS", "Hanya optimal dengan device Apple", "Bass kurang kuat untuk bass-head"],
            summary="TWS terbaik untuk pengguna Apple dengan ANC dan fitur AI audio paling canggih."
        ),
        warranty=WarrantyInfo(
            duration_months=12,
            coverage="Garansi resmi Apple — hardware, bisa AppleCare+",
            claim_ease=9,
            official_service_centers=45,
            score=88.0
        ),
        marketplace_links={
            "tokopedia": "https://www.tokopedia.com/search?q=airpods+pro+2+usb-c",
            "shopee": "https://shopee.co.id/search?keyword=airpods+pro+2+usb-c",
            "lazada": "https://www.lazada.co.id/catalog/?q=airpods+pro+2+usb-c"
        },
        tags=["tws", "anc", "apple", "premium", "spatial-audio"],
        release_year=2023,
        score_performance=70,
        score_camera=0,
        score_battery=82,
        score_display=0,
        score_build_quality=88,
        score_value=65,
        score_audio=95,
        score_software=92
    ),
    Product(
        id="tw-002",
        name="Sony WF-1000XM5",
        brand="Sony",
        category=ProductCategory.TWS,
        price=4299000,
        image="/images/sony-wf1000xm5.webp",
        description="TWS audiophile-grade Sony dengan ANC terbaik, LDAC support, dan suara Hi-Res.",
        specs=ProductSpecs(
            display="N/A",
            battery="8h (ANC On) + 24h (Case)",
            connectivity="Bluetooth 5.3",
            weight="5.9g per earbud",
            water_resistance="IPX4",
            driver_size="8.4mm Dynamic Driver",
            anc="Dual Noise Sensor + Adaptive Sound Control",
            codec="LDAC, AAC, SBC, LC3",
            build_material="Soft-fit Polyurethane Foam Tips",
            special_features="LDAC Hi-Res, Speak-to-Chat, DSEE Extreme, Multipoint"
        ),
        review_sentiment=ReviewSentiment(
            overall_score=4.6,
            total_reviews=9800,
            pros=["Suara Hi-Res LDAC terbaik", "ANC sangat efektif", "Compact & ringan", "Multipoint connect 2 device", "Battery life sangat baik"],
            cons=["Harga paling mahal di TWS", "Foam tips cepat aus", "IPX4 bukan IP68"],
            summary="TWS audiophile terbaik dengan suara Hi-Res LDAC dan ANC kelas dunia."
        ),
        warranty=WarrantyInfo(
            duration_months=12,
            coverage="Garansi resmi Sony Indonesia — hardware",
            claim_ease=7,
            official_service_centers=80,
            score=75.0
        ),
        marketplace_links={
            "tokopedia": "https://www.tokopedia.com/search?q=sony+wf-1000xm5",
            "shopee": "https://shopee.co.id/search?keyword=sony+wf-1000xm5",
            "lazada": "https://www.lazada.co.id/catalog/?q=sony+wf-1000xm5"
        },
        tags=["tws", "anc", "hi-res", "ldac", "audiophile"],
        release_year=2023,
        score_performance=70,
        score_camera=0,
        score_battery=88,
        score_display=0,
        score_build_quality=85,
        score_value=60,
        score_audio=98,
        score_software=82
    ),
    Product(
        id="tw-003",
        name="Samsung Galaxy Buds3 Pro",
        brand="Samsung",
        category=ProductCategory.TWS,
        price=3299000,
        image="/images/galaxy-buds3-pro.webp",
        description="TWS Samsung terbaru dengan desain blade, ANC canggih, dan Galaxy AI features.",
        specs=ProductSpecs(
            display="N/A",
            battery="7h (ANC On) + 30h (Case)",
            connectivity="Bluetooth 5.4",
            weight="5.4g per earbud",
            water_resistance="IP57",
            driver_size="10.5mm Planar + 6.1mm Tweeter (2-way)",
            anc="Adaptive ANC + Ambient Sound",
            codec="SSC HiFi, AAC, SBC, Scalable Codec",
            build_material="Blade Design, Glossy Finish",
            special_features="Galaxy AI Interpreter, 2-Way Speaker, 360 Audio, Blade Lights"
        ),
        review_sentiment=ReviewSentiment(
            overall_score=4.3,
            total_reviews=4500,
            pros=["Desain blade stylish", "2-way speaker suara detail", "Galaxy AI interpreter unik", "IP57 tahan air", "360 Audio immersive"],
            cons=["Desain blade tidak nyaman untuk semua telinga", "Galaxy AI butuh Samsung phone", "Blade lights gimmicky"],
            summary="TWS Samsung paling canggih dengan desain blade dan fitur Galaxy AI."
        ),
        warranty=WarrantyInfo(
            duration_months=12,
            coverage="Garansi resmi Samsung Indonesia — hardware",
            claim_ease=8,
            official_service_centers=350,
            score=82.0
        ),
        marketplace_links={
            "tokopedia": "https://www.tokopedia.com/search?q=samsung+galaxy+buds3+pro",
            "shopee": "https://shopee.co.id/search?keyword=samsung+galaxy+buds3+pro",
            "lazada": "https://www.lazada.co.id/catalog/?q=samsung+galaxy+buds3+pro"
        },
        tags=["tws", "anc", "galaxy-ai", "blade-design", "2-way-speaker"],
        release_year=2024,
        score_performance=70,
        score_camera=0,
        score_battery=85,
        score_display=0,
        score_build_quality=80,
        score_value=72,
        score_audio=90,
        score_software=85
    ),

    # ═══════════════════════════════════════════
    # SMARTWATCHES
    # ═══════════════════════════════════════════
    Product(
        id="sw-001",
        name="Apple Watch Ultra 2",
        brand="Apple",
        category=ProductCategory.SMARTWATCH,
        price=13999000,
        image="/images/apple-watch-ultra-2.webp",
        description="Smartwatch paling tangguh Apple untuk adventure & diving dengan layar 2000 nits.",
        specs=ProductSpecs(
            display="1.93\" LTPO OLED Always-On, 502x410",
            processor="Apple S9 SiP",
            battery="Up to 36 hours (72h Low Power)",
            connectivity="Wi-Fi, Bluetooth 5.3, UWB, LTE Cellular",
            weight="61.4g",
            water_resistance="WR100 + EN13319 (Diving 40m)",
            screen_size="49mm",
            resolution="502 x 410",
            build_material="Titanium Case, Sapphire Crystal",
            sensors="Heart Rate, ECG, SpO2, Temperature, Depth Gauge, Altimeter",
            special_features="Double Tap, Precision GPS (L1+L5), Action Button, Siren 86dB"
        ),
        review_sentiment=ReviewSentiment(
            overall_score=4.7,
            total_reviews=6800,
            pros=["Layar 2000 nits terbaca di matahari", "Build titanium super tangguh", "GPS paling akurat", "Fitur diving profesional", "Baterai 36 jam cukup"],
            cons=["Sangat mahal", "Ukuran 49mm terlalu besar untuk pergelangan kecil", "Hanya untuk iPhone"],
            summary="Smartwatch adventure terbaik untuk atlet, diver, dan outdoor enthusiast."
        ),
        warranty=WarrantyInfo(
            duration_months=12,
            coverage="Garansi resmi Apple — hardware, bisa AppleCare+",
            claim_ease=9,
            official_service_centers=45,
            score=88.0
        ),
        marketplace_links={
            "tokopedia": "https://www.tokopedia.com/search?q=apple+watch+ultra+2",
            "shopee": "https://shopee.co.id/search?keyword=apple+watch+ultra+2",
            "lazada": "https://www.lazada.co.id/catalog/?q=apple+watch+ultra+2"
        },
        tags=["smartwatch", "adventure", "titanium", "diving", "premium"],
        release_year=2023,
        score_performance=90,
        score_camera=0,
        score_battery=85,
        score_display=95,
        score_build_quality=98,
        score_value=50,
        score_audio=75,
        score_software=92
    ),
    Product(
        id="sw-002",
        name="Samsung Galaxy Watch 7",
        brand="Samsung",
        category=ProductCategory.SMARTWATCH,
        price=4499000,
        image="/images/galaxy-watch-7.webp",
        description="Smartwatch Android terbaik dengan Wear OS 5, BioActive Sensor 3.0, dan AI health insights.",
        specs=ProductSpecs(
            display="1.3\" Super AMOLED Always-On, 432x432",
            processor="Exynos W1000 (3nm)",
            battery="Up to 40 hours",
            connectivity="Wi-Fi, Bluetooth 5.3, NFC, LTE Optional",
            weight="33.8g (40mm)",
            water_resistance="5ATM + IP68 + MIL-STD-810H",
            screen_size="40mm / 44mm",
            resolution="432 x 432",
            build_material="Armor Aluminum, Sapphire Crystal",
            sensors="BioActive 3.0 (Heart Rate, ECG, BIA, SpO2, Temperature)",
            special_features="Galaxy AI Health, Energy Score, Sleep Coaching, Wear OS 5"
        ),
        review_sentiment=ReviewSentiment(
            overall_score=4.3,
            total_reviews=7200,
            pros=["Exynos W1000 3nm super smooth", "Galaxy AI health insights berguna", "Wear OS 5 fluid", "BioActive sensor lengkap", "Harga reasonable"],
            cons=["Baterai 1-2 hari saja", "Bezel agak tebal", "Google Assistant kadang lambat"],
            summary="Smartwatch Android terbaik dengan health tracking terlengkap dan prosesor 3nm tercepat."
        ),
        warranty=WarrantyInfo(
            duration_months=12,
            coverage="Garansi resmi Samsung Indonesia — hardware",
            claim_ease=8,
            official_service_centers=350,
            score=82.0
        ),
        marketplace_links={
            "tokopedia": "https://www.tokopedia.com/search?q=samsung+galaxy+watch+7",
            "shopee": "https://shopee.co.id/search?keyword=samsung+galaxy+watch+7",
            "lazada": "https://www.lazada.co.id/catalog/?q=samsung+galaxy+watch+7"
        },
        tags=["smartwatch", "wear-os", "galaxy-ai", "health", "3nm"],
        release_year=2024,
        score_performance=82,
        score_camera=0,
        score_battery=70,
        score_display=88,
        score_build_quality=82,
        score_value=78,
        score_audio=60,
        score_software=85
    ),

    # ═══════════════════════════════════════════
    # ADDITIONAL SMARTPHONES (mid-range)
    # ═══════════════════════════════════════════
    Product(
        id="sm-006",
        name="Samsung Galaxy A55 5G",
        brand="Samsung",
        category=ProductCategory.SMARTPHONE,
        price=5499000,
        image="/images/galaxy-a55.webp",
        description="Mid-range Samsung terbaik dengan layar Super AMOLED 120Hz, Exynos 1480, dan IP67.",
        specs=ProductSpecs(
            display="6.6\" Super AMOLED, 2340x1080",
            processor="Samsung Exynos 1480",
            ram="8 GB / 12 GB",
            storage="128 GB / 256 GB + microSD",
            battery="5000 mAh",
            camera="50MP + 12MP + 5MP",
            os="Android 14 (One UI 6.1)",
            weight="213g",
            connectivity="5G, Wi-Fi 6, Bluetooth 5.3",
            refresh_rate="120Hz",
            resolution="2340 x 1080 (FHD+)",
            water_resistance="IP67",
            build_material="Glass Back, Metal Frame",
            special_features="4 Gen OS Update, 5 Gen Security, Samsung Knox"
        ),
        review_sentiment=ReviewSentiment(
            overall_score=4.3,
            total_reviews=9800,
            pros=["Layar AMOLED tajam dan cerah", "IP67 di harga mid-range", "4 generasi OS update", "Kamera utama 50MP baik", "Build quality premium glass-metal"],
            cons=["Exynos 1480 kurang untuk heavy gaming", "Charging hanya 25W", "Kamera ultrawide biasa saja"],
            summary="Mid-range Samsung terbaik dengan durabilitas, update panjang, dan layar AMOLED."
        ),
        warranty=WarrantyInfo(
            duration_months=12,
            coverage="Garansi resmi Samsung Indonesia — hardware",
            claim_ease=8,
            official_service_centers=350,
            score=82.0
        ),
        marketplace_links={
            "tokopedia": "https://www.tokopedia.com/search?q=samsung+galaxy+a55+5g",
            "shopee": "https://shopee.co.id/search?keyword=samsung+galaxy+a55+5g",
            "lazada": "https://www.lazada.co.id/catalog/?q=samsung+galaxy+a55+5g"
        },
        tags=["mid-range", "5g", "ip67", "amoled", "long-update"],
        release_year=2024,
        score_performance=72,
        score_camera=72,
        score_battery=82,
        score_display=82,
        score_build_quality=80,
        score_value=85,
        score_audio=70,
        score_software=85
    ),

    # ═══════════════════════════════════════════
    # ADDITIONAL LAPTOP (budget gaming)
    # ═══════════════════════════════════════════
    Product(
        id="lp-005",
        name="Lenovo LOQ 15IRX9",
        brand="Lenovo",
        category=ProductCategory.LAPTOP,
        price=13999000,
        image="/images/lenovo-loq-15.webp",
        description="Laptop gaming budget dengan Intel Core i5 Gen 13, RTX 4050, dan layar 144Hz.",
        specs=ProductSpecs(
            display="15.6\" IPS FHD, 1920x1080",
            processor="Intel Core i5-13450HX",
            ram="16 GB DDR5",
            storage="512 GB PCIe Gen4 SSD",
            battery="60 Wh",
            os="Windows 11 Home",
            weight="2.38 kg",
            connectivity="Wi-Fi 6, Bluetooth 5.1",
            screen_size="15.6 inch",
            gpu="NVIDIA GeForce RTX 4050 6GB",
            resolution="1920 x 1080 (FHD)",
            refresh_rate="144Hz",
            build_material="Plastic Body, Metal Lid",
            special_features="Nahimic Audio, Lenovo LA AI Chip, 100W PD Charging"
        ),
        review_sentiment=ReviewSentiment(
            overall_score=4.2,
            total_reviews=6800,
            pros=["RTX 4050 bisa main AAA games", "Harga paling value di kelas gaming", "Layar 144Hz smooth", "DDR5 + SSD NVMe Gen4 cepat", "Thermal cukup baik"],
            cons=["Build quality plastik", "Layar kurang terang (250 nits)", "Speaker biasa saja", "Agak berat 2.38kg"],
            summary="Best value gaming laptop untuk entry-level gamer yang butuh RTX 4050 di budget terbatas."
        ),
        warranty=WarrantyInfo(
            duration_months=24,
            coverage="Garansi resmi Lenovo Indonesia — 2 tahun hardware, ADP optional",
            claim_ease=8,
            official_service_centers=200,
            score=85.0
        ),
        marketplace_links={
            "tokopedia": "https://www.tokopedia.com/search?q=lenovo+loq+15irx9",
            "shopee": "https://shopee.co.id/search?keyword=lenovo+loq+15irx9",
            "lazada": "https://www.lazada.co.id/catalog/?q=lenovo+loq+15irx9"
        },
        tags=["gaming", "budget", "rtx-4050", "144hz", "value"],
        release_year=2024,
        score_performance=80,
        score_camera=30,
        score_battery=55,
        score_display=70,
        score_build_quality=60,
        score_value=88,
        score_audio=55,
        score_software=72
    ),

    # ═══════════════════════════════════════════
    # ADDITIONAL TWS (budget)
    # ═══════════════════════════════════════════
    Product(
        id="tw-004",
        name="QCY MeloBuds ANC",
        brand="QCY",
        category=ProductCategory.TWS,
        price=349000,
        image="/images/qcy-melobuds.webp",
        description="TWS budget dengan ANC aktif, driver 10mm, dan baterai 30 jam — dibawah 400 ribu.",
        specs=ProductSpecs(
            display="N/A",
            battery="7.5h (ANC On) + 30h (Case)",
            connectivity="Bluetooth 5.3",
            weight="4.7g per earbud",
            water_resistance="IPX5",
            driver_size="10mm Dynamic Driver",
            anc="Hybrid ANC -43dB",
            codec="AAC, SBC",
            build_material="Plastic, Silicone Tips",
            special_features="App EQ Customization, Game Mode 60ms, Transparency Mode"
        ),
        review_sentiment=ReviewSentiment(
            overall_score=4.1,
            total_reviews=15600,
            pros=["Harga sangat murah", "ANC berfungsi di harga segini", "Baterai tahan lama", "Nyaman di telinga", "App QCY cukup lengkap"],
            cons=["Build quality plastik tipis", "Mikrofon biasa saja untuk call", "Bass kurang dalam", "Tidak ada LDAC"],
            summary="TWS budget terbaik yang punya ANC aktif dengan harga di bawah 400 ribu."
        ),
        warranty=WarrantyInfo(
            duration_months=6,
            coverage="Garansi distributor — 6 bulan",
            claim_ease=4,
            official_service_centers=20,
            score=40.0
        ),
        marketplace_links={
            "tokopedia": "https://www.tokopedia.com/search?q=qcy+melobuds+anc",
            "shopee": "https://shopee.co.id/search?keyword=qcy+melobuds+anc",
            "lazada": "https://www.lazada.co.id/catalog/?q=qcy+melobuds+anc"
        },
        tags=["tws", "budget", "anc", "value", "affordable"],
        release_year=2024,
        score_performance=45,
        score_camera=0,
        score_battery=85,
        score_display=0,
        score_build_quality=40,
        score_value=97,
        score_audio=62,
        score_software=50
    ),

    # ═══════════════════════════════════════════
    # ADDITIONAL SMARTWATCH (budget)
    # ═══════════════════════════════════════════
    Product(
        id="sw-003",
        name="Amazfit GTR 4",
        brand="Amazfit",
        category=ProductCategory.SMARTWATCH,
        price=2999000,
        image="/images/amazfit-gtr4.webp",
        description="Smartwatch premium-look dengan AMOLED display, GPS dual-band, dan baterai 14 hari.",
        specs=ProductSpecs(
            display="1.43\" AMOLED, 466x466",
            processor="Custom Zepp OS Chip",
            battery="Up to 14 days",
            connectivity="Wi-Fi, Bluetooth 5.0, GPS",
            weight="52g (without strap)",
            water_resistance="5ATM",
            screen_size="46mm",
            resolution="466 x 466",
            build_material="Aluminum Alloy, Glass",
            sensors="BioTracker 4.0 PPG, SpO2, Accelerometer, Gyro, Barometer",
            special_features="Zepp OS, 150+ Sports Modes, Alexa Built-in, Route Navigation"
        ),
        review_sentiment=ReviewSentiment(
            overall_score=4.3,
            total_reviews=8900,
            pros=["Baterai 14 hari luar biasa", "Layar AMOLED tajam", "GPS dual-band akurat", "Desain premium dengan harga terjangkau", "150+ sport modes"],
            cons=["App ecosystem terbatas", "Notifikasi reply terbatas", "Zepp OS kurang fleksibel"],
            summary="Smartwatch best-value dengan baterai marathon, layar AMOLED, dan GPS akurat."
        ),
        warranty=WarrantyInfo(
            duration_months=12,
            coverage="Garansi resmi Amazfit Indonesia — hardware",
            claim_ease=6,
            official_service_centers=50,
            score=62.0
        ),
        marketplace_links={
            "tokopedia": "https://www.tokopedia.com/search?q=amazfit+gtr+4",
            "shopee": "https://shopee.co.id/search?keyword=amazfit+gtr+4",
            "lazada": "https://www.lazada.co.id/catalog/?q=amazfit+gtr+4"
        },
        tags=["smartwatch", "amoled", "14-day-battery", "gps", "value"],
        release_year=2023,
        score_performance=65,
        score_camera=0,
        score_battery=95,
        score_display=82,
        score_build_quality=72,
        score_value=90,
        score_audio=40,
        score_software=60
    ),
]


def get_all_products() -> list[Product]:
    return PRODUCTS


def get_product_by_id(product_id: str) -> Product | None:
    for p in PRODUCTS:
        if p.id == product_id:
            return p
    return None


def get_products_by_category(category: str) -> list[Product]:
    return [p for p in PRODUCTS if p.category.value == category]


def get_unique_brands() -> list[str]:
    return sorted(set(p.brand for p in PRODUCTS))


def get_unique_tags() -> list[str]:
    tags = set()
    for p in PRODUCTS:
        tags.update(p.tags)
    return sorted(tags)


def search_products(query: str) -> list[Product]:
    q = query.lower()
    results = []
    for p in PRODUCTS:
        if (q in p.name.lower() or
            q in p.brand.lower() or
            q in p.description.lower() or
            any(q in tag for tag in p.tags)):
            results.append(p)
    return results
