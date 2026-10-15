"""
CompareBuy — Integration Tests: Curated Product Catalog (PostgreSQL)
Fitur 3 – MVP Version 1

Menguji endpoint GET /api/products (backend/app/routers/catalog.py) yang membaca
produk dari tabel PostgreSQL lewat SQLAlchemy (app/repositories/catalog_repo.py).

PRASYARAT
    Sediakan database PostgreSQL KHUSUS pengujian (kosong, nama mengandung "test"):

        CREATE DATABASE comparebuy_test;

    lalu set variabel lingkungan (jangan commit password ke repository):

        $env:TEST_DATABASE_URL = "postgresql://USER:PASSWORD@localhost:5432/comparebuy_test"

    Tanpa TEST_DATABASE_URL, seluruh modul ini di-SKIP (tidak pernah diganti SQLite
    atau dataset in-memory).

KEAMANAN
    - URL harus PostgreSQL, nama database harus mengandung "test", dan tidak boleh
      sama dengan DATABASE_URL (database development/production) -> jika tidak, ditolak.
    - Tes tidak pernah DROP/DELETE/TRUNCATE. Setiap tes berjalan di dalam transaksi
      (SAVEPOINT) yang selalu di-ROLLBACK, sehingga database test tetap kosong.
    - Password tidak pernah dicetak.

Fixture produk dimasukkan ke tabel database (ID berawalan "pgt-"), bukan dari
konstanta katalog di app/products.py, sehingga hasil tes membuktikan data dibaca
dari PostgreSQL.
Menggunakan standar library unittest Python.
"""
import sys
import os
import subprocess
import unittest

# Pastikan modul app dapat diimpor dari direktori backend
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tests import _pretty  # noqa: F401  (format output [OK] ...)

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text, func
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.main import app
from app.db import get_db, DATABASE_URL as DEV_DATABASE_URL
from app.entities import (
    Brand, Product, ProductSpecs, ReviewSentiment, WarrantyInfo, Tag, ProductTag,
)
from app.products import get_all_products

client = TestClient(app)

_engine = None
_TEST_DB_NAME = None

# ──────────────────────────────────────────────────────────────────
# Fixture katalog (dimasukkan ke PostgreSQL). Atribut sengaja beragam.
# ──────────────────────────────────────────────────────────────────
FIXTURES = [
    dict(id="pgt-001", name="Alpha Phone One", brand="AlphaTech", category="smartphone",
         price=3_000_000, score=90, tags=["gaming", "5g"], description="Ponsel gaming alpha"),
    dict(id="pgt-002", name="Alpha Phone Two", brand="AlphaTech", category="smartphone",
         price=7_500_000, score=70, tags=["5g", "camera"], description="Ponsel kamera alpha"),
    dict(id="pgt-003", name="Beta Book Air", brand="BetaWorks", category="laptop",
         price=12_000_000, score=80, tags=["ultrabook", "student"], description="Laptop tipis beta"),
    dict(id="pgt-004", name="Beta Book Pro", brand="BetaWorks", category="laptop",
         price=25_000_000, score=95, tags=["gaming", "creator"], description="Laptop kreator beta"),
    dict(id="pgt-005", name="Gamma Buds", brand="GammaLabs", category="tws",
         price=500_000, score=60, tags=["anc"], description="Earbuds gamma"),
    dict(id="pgt-006", name="Gamma Watch", brand="GammaLabs", category="smartwatch",
         price=2_000_000, score=75, tags=["health", "5g"], description="Jam tangan gamma"),
    dict(id="pgt-007", name="Delta Tab", brand="AlphaTech", category="tablet",
         price=9_000_000, score=65, tags=["student"], description="Tablet delta"),
    dict(id="pgt-008", name="Inactive Phone", brand="AlphaTech", category="smartphone",
         price=1_000_000, score=99, tags=["gaming"], description="Tidak aktif", is_active=False),
]
ACTIVE_IDS = [f["id"] for f in FIXTURES if f.get("is_active", True)]  # 7 produk aktif


def _insert_product(session: Session, spec: dict) -> Product:
    """Masukkan satu produk lengkap (brand, specs, sentimen, garansi, tags) ke database."""
    brand = session.query(Brand).filter(Brand.name == spec["brand"]).first()
    if brand is None:
        brand = Brand(name=spec["brand"])
        session.add(brand)
        session.flush()

    s = spec["score"]
    product = Product(
        id=spec["id"], name=spec["name"], brand_id=brand.id, category=spec["category"],
        price=spec["price"], description=spec["description"], release_year=2024,
        score_performance=s, score_camera=s, score_battery=s, score_display=s,
        score_build_quality=s, score_value=s, score_audio=s, score_software=s,
        is_active=spec.get("is_active", True),
    )
    session.add(product)
    session.flush()

    session.add(ProductSpecs(product_id=spec["id"], specifications={"display": f"Layar {spec['name']}"}))
    session.add(ReviewSentiment(
        product_id=spec["id"], overall_score=4.2, total_reviews=100,
        pros=[f"Kelebihan {spec['name']}"], cons=[f"Kekurangan {spec['name']}"], summary="Ringkasan",
    ))
    session.add(WarrantyInfo(
        product_id=spec["id"], duration_months=12, coverage="Garansi resmi - hardware",
        claim_ease=7, official_service_centers=5, score=80.0,
    ))
    for tag_name in spec["tags"]:
        tag = session.query(Tag).filter(Tag.name == tag_name).first()
        if tag is None:
            tag = Tag(name=tag_name)
            session.add(tag)
            session.flush()
        session.add(ProductTag(product_id=spec["id"], tag_id=tag.id))
    session.flush()
    return product


def _resolve_test_database_url():
    """Validasi ketat TEST_DATABASE_URL. Tidak pernah mencetak password."""
    raw = os.environ.get("TEST_DATABASE_URL")
    if not raw:
        raise unittest.SkipTest(
            "TEST_DATABASE_URL belum diset — tes integrasi katalog membutuhkan PostgreSQL "
            "khusus pengujian (mis. CREATE DATABASE comparebuy_test; lalu set "
            "TEST_DATABASE_URL). Tes TIDAK dijalankan."
        )
    try:
        url = make_url(raw)
    except Exception:
        raise RuntimeError("TEST_DATABASE_URL bukan URL database yang valid.") from None

    if url.get_backend_name() not in ("postgresql", "postgres"):
        raise RuntimeError(
            f"TEST_DATABASE_URL harus PostgreSQL, bukan '{url.get_backend_name()}' "
            "(SQLite/in-memory tidak diizinkan)."
        )
    url = url.set(drivername="postgresql+psycopg2")

    if "test" not in (url.database or "").lower():
        raise RuntimeError(
            "Nama database pada TEST_DATABASE_URL harus mengandung 'test' "
            f"(ditolak: '{url.database}')."
        )

    if DEV_DATABASE_URL:
        dev = make_url(DEV_DATABASE_URL)
        if (dev.host, dev.port or 5432, dev.database) == (url.host, url.port or 5432, url.database):
            raise RuntimeError(
                "TEST_DATABASE_URL menunjuk ke database yang sama dengan DATABASE_URL "
                "(development/production). Pengujian dibatalkan."
            )
    return url


def setUpModule():
    """Hubungkan ke PostgreSQL test, buat schema (non-destruktif), pastikan database kosong."""
    global _engine, _TEST_DB_NAME
    url = _resolve_test_database_url()
    safe = url.render_as_string(hide_password=True)
    engine = create_engine(url, pool_pre_ping=True)
    try:
        with engine.connect() as conn:
            current = conn.execute(text("select current_database()")).scalar()
            version = conn.execute(text("select version()")).scalar()
    except Exception as exc:
        engine.dispose()
        raise RuntimeError(
            f"Tidak bisa terhubung ke PostgreSQL test ({safe}): {type(exc).__name__}"
        ) from None

    if current != url.database or "PostgreSQL" not in version:
        engine.dispose()
        raise RuntimeError(f"Koneksi test tidak menunjuk PostgreSQL '{url.database}'.")

    # Inisialisasi schema dengan Alembic (mekanisme migrasi resmi repository: 001 + 002).
    # migrations/env.py selalu memakai DATABASE_URL, sehingga dijalankan di SUBPROCESS dengan
    # DATABASE_URL diarahkan ke database test (load_dotenv tidak menimpa variabel yang sudah ada).
    # Hanya CREATE/ALTER pada database test; tidak ada DROP/DELETE.
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    env = dict(os.environ, DATABASE_URL=url.render_as_string(hide_password=False))
    proc = subprocess.run(
        [sys.executable, "-m", "alembic", "-c", "alembic.ini", "upgrade", "head"],
        cwd=backend_dir, env=env, capture_output=True, text=True, timeout=180,
    )
    if proc.returncode != 0:
        engine.dispose()
        output = (proc.stdout or "") + (proc.stderr or "")
        if url.password:
            output = output.replace(url.password, "***")
        raise RuntimeError(f"Alembic upgrade pada database test gagal ({safe}):\n{output[-1500:]}")

    with Session(engine) as check:
        leftovers = {
            "products": check.query(func.count(Product.id)).scalar(),
            "brands": check.query(func.count(Brand.id)).scalar(),
            "tags": check.query(func.count(Tag.id)).scalar(),
        }
    if any(leftovers.values()):
        engine.dispose()
        raise RuntimeError(
            f"Database test '{current}' tidak kosong {leftovers}. Gunakan database kosong "
            "khusus pengujian; tes tidak akan menghapus data apa pun."
        )

    _engine = engine
    _TEST_DB_NAME = current


def tearDownModule():
    global _engine
    app.dependency_overrides.pop(get_db, None)
    if _engine is not None:
        _engine.dispose()
        _engine = None


class PostgresCatalogTestCase(unittest.TestCase):
    """Setiap tes: koneksi + transaksi sendiri, fixture di-insert, lalu di-ROLLBACK."""

    def setUp(self):
        self.connection = _engine.connect()
        self.transaction = self.connection.begin()
        self.session = Session(bind=self.connection, join_transaction_mode="create_savepoint")

        def _override_get_db():
            yield self.session

        app.dependency_overrides[get_db] = _override_get_db
        for spec in FIXTURES:
            _insert_product(self.session, spec)

    def tearDown(self):
        app.dependency_overrides.pop(get_db, None)
        self.session.close()
        self.transaction.rollback()
        self.connection.close()

    def get(self, params: str = ""):
        return client.get(f"/api/products?{params}")

    def ids(self, params: str = "") -> list:
        res = self.get(params)
        self.assertEqual(res.status_code, 200, msg=res.text)
        return [p["id"] for p in res.json()["products"]]


# ═══════════════════════════════════════════════════════════════════
# Test Suite 1 — Bukti Koneksi & Sumber Data PostgreSQL
# ═══════════════════════════════════════════════════════════════════
class TestPostgresIntegration(PostgresCatalogTestCase):
    """Membuktikan endpoint membaca tabel PostgreSQL test, bukan dataset in-memory."""

    def test_session_is_connected_to_postgresql(self):
        """Session test benar-benar terhubung ke PostgreSQL (dialect dan versi server)"""
        self.assertEqual(self.session.get_bind().dialect.name, "postgresql")
        version = self.session.execute(text("select version()")).scalar()
        self.assertIn("PostgreSQL", version)

    def test_session_uses_isolated_test_database(self):
        """Database yang dipakai adalah database test, bukan database development"""
        current = self.session.execute(text("select current_database()")).scalar()
        self.assertEqual(current, _TEST_DB_NAME)
        self.assertIn("test", current.lower())
        if DEV_DATABASE_URL:
            self.assertNotEqual(current, make_url(DEV_DATABASE_URL).database)

    def test_endpoint_returns_only_database_fixture_rows(self):
        """Endpoint hanya mengembalikan produk fixture di database (7 aktif), bukan 20 produk memori"""
        data = self.get("per_page=100").json()
        self.assertEqual(data["total"], len(ACTIVE_IDS))
        self.assertEqual(sorted(p["id"] for p in data["products"]), sorted(ACTIVE_IDS))
        in_memory_ids = {p.id for p in get_all_products()}
        self.assertFalse(in_memory_ids & {p["id"] for p in data["products"]})

    def test_inactive_product_is_excluded(self):
        """Produk dengan is_active=False di database tidak pernah muncul di katalog"""
        self.assertNotIn("pgt-008", self.ids("per_page=100"))

    def test_changing_database_fixture_changes_response(self):
        """Mengubah baris di database langsung mengubah respons (bukan konstanta memori)"""
        before = self.get("per_page=100").json()
        self.assertEqual(before["total"], 7)

        # (1) tambah produk baru
        _insert_product(self.session, dict(
            id="pgt-009", name="Epsilon Phone", brand="EpsilonCo", category="smartphone",
            price=4_000_000, score=85, tags=["5g"], description="Produk baru"))
        after_insert = self.get("per_page=100").json()
        self.assertEqual(after_insert["total"], 8)
        self.assertIn("pgt-009", [p["id"] for p in after_insert["products"]])

        # (2) ubah harga produk
        self.session.query(Product).filter(Product.id == "pgt-001").update({"price": 123_456})
        self.session.flush()
        prices = {p["id"]: p["price"] for p in self.get("per_page=100").json()["products"]}
        self.assertEqual(prices["pgt-001"], 123_456)

        # (3) nonaktifkan produk
        self.session.query(Product).filter(Product.id == "pgt-002").update({"is_active": False})
        self.session.flush()
        self.assertNotIn("pgt-002", self.ids("per_page=100"))

    def test_rollback_leaves_database_empty_between_tests(self):
        """Data fixture tidak bocor antar tes: transaksi selalu di-rollback (urutan tes tidak berpengaruh)"""
        self.assertEqual(self.session.query(func.count(Product.id)).scalar(), len(FIXTURES))
        with _engine.connect() as other_connection:
            visible = other_connection.execute(text("select count(*) from products")).scalar()
        self.assertEqual(visible, 0, msg="Fixture tidak boleh ter-commit ke database test")


# ═══════════════════════════════════════════════════════════════════
# Test Suite 2 — Filter Kategori, Brand, Tags, & Pencarian Teks
# ═══════════════════════════════════════════════════════════════════
class TestCatalogFilters(PostgresCatalogTestCase):
    """Memastikan filter multi-kriteria dieksekusi di PostgreSQL dan menghasilkan irisan benar."""

    def test_filter_by_category(self):
        """category=laptop hanya mengembalikan 2 laptop fixture"""
        self.assertEqual(sorted(self.ids("category=laptop")), ["pgt-003", "pgt-004"])

    def test_filter_by_category_without_rows_returns_empty(self):
        """Kategori valid tanpa produk aktif tetap dilayani database: daftar kosong, total 0"""
        self.session.query(Product).filter(Product.category == "tws").update({"is_active": False})
        self.session.flush()
        data = self.get("category=tws").json()
        self.assertEqual(data["products"], [])
        self.assertEqual(data["total"], 0)

    def test_filter_by_brand_is_case_insensitive(self):
        """brand=alphatech (huruf kecil) cocok dengan brand 'AlphaTech' (3 aktif)"""
        self.assertEqual(sorted(self.ids("brand=alphatech")), ["pgt-001", "pgt-002", "pgt-007"])

    def test_filter_by_single_tag(self):
        """tags=5g hanya mengembalikan produk bertag 5g"""
        self.assertEqual(sorted(self.ids("tags=5g")), ["pgt-001", "pgt-002", "pgt-006"])

    def test_text_search_matches_name_and_description(self):
        """search menemukan produk lewat nama dan lewat deskripsi"""
        self.assertEqual(self.ids("search=buds"), ["pgt-005"])
        self.assertEqual(self.ids("search=kreator"), ["pgt-004"])

    def test_text_search_without_match_returns_empty(self):
        """Pencarian tanpa hasil mengembalikan daftar kosong dan total 0"""
        data = self.get("search=produk-tidak-ada-xyz").json()
        self.assertEqual(data["products"], [])
        self.assertEqual(data["total"], 0)

    def test_price_range_filter_within_bounds(self):
        """min_price/max_price hanya mengembalikan produk dalam rentang harga (inklusif)"""
        self.assertEqual(
            sorted(self.ids("min_price=2000000&max_price=9000000")),
            ["pgt-001", "pgt-002", "pgt-006", "pgt-007"],
        )

    def test_price_filter_boundaries_are_inclusive(self):
        """Harga tepat sama dengan min_price atau max_price ikut terhitung"""
        self.assertEqual(self.ids("min_price=7500000&max_price=7500000"), ["pgt-002"])

    def test_only_max_price_filter(self):
        """Hanya max_price: semua produk dengan harga <= batas"""
        self.assertEqual(sorted(self.ids("max_price=2000000")), ["pgt-005", "pgt-006"])

    def test_combined_category_brand_and_price(self):
        """Kombinasi category+brand+min_price hanya mengembalikan irisan (pgt-002)"""
        self.assertEqual(self.ids("category=smartphone&brand=AlphaTech&min_price=5000000"), ["pgt-002"])

    def test_combined_filter_with_sorting(self):
        """Kombinasi tags+price dengan sortir price_desc mengikuti urutan harga"""
        self.assertEqual(self.ids("tags=gaming&sort_by=price_desc"), ["pgt-004", "pgt-001"])
        self.assertEqual(self.ids("tags=gaming&sort_by=price_asc"), ["pgt-001", "pgt-004"])
        self.assertEqual(self.ids("tags=5g&min_price=3000000&sort_by=name"), ["pgt-001", "pgt-002"])

    def test_total_is_consistent_with_filtered_items(self):
        """Nilai total selalu sama dengan jumlah item hasil filter (per_page besar)"""
        for params in ("category=smartphone", "brand=GammaLabs", "tags=student", "max_price=3000000"):
            data = self.get(params + "&per_page=100").json()
            self.assertEqual(data["total"], len(data["products"]), msg=params)


# ═══════════════════════════════════════════════════════════════════
# Test Suite 3 — Validasi Boundary Rentang Harga
# ═══════════════════════════════════════════════════════════════════
class TestCatalogPriceRangeValidation(PostgresCatalogTestCase):
    """Memastikan rentang harga terbalik ditolak dengan 422."""

    def test_min_price_greater_than_max_price_returns_422(self):
        """min_price > max_price harus mengembalikan HTTP 422"""
        self.assertEqual(self.get("min_price=10000000&max_price=5000000").status_code, 422)

    def test_min_price_greater_than_max_price_error_message(self):
        """Pesan error harus persis sesuai acceptance criteria"""
        res = self.get("min_price=10000000&max_price=5000000")
        self.assertEqual(res.json()["detail"], "min_price tidak boleh lebih besar dari max_price.")

    def test_min_price_equal_to_max_price_is_allowed(self):
        """min_price == max_price bukan rentang terbalik: HTTP 200 dan hasil dari database"""
        self.assertEqual(self.ids("min_price=3000000&max_price=3000000"), ["pgt-001"])

    def test_only_min_price_does_not_trigger_validation(self):
        """Hanya min_price (tanpa max_price) tetap valid"""
        self.assertEqual(sorted(self.ids("min_price=12000000")), ["pgt-003", "pgt-004"])

    def test_negative_price_returns_422(self):
        """Harga negatif ditolak dengan HTTP 422"""
        self.assertEqual(self.get("min_price=-1").status_code, 422)
        self.assertEqual(self.get("max_price=-1").status_code, 422)


# ═══════════════════════════════════════════════════════════════════
# Test Suite 4 — Pengurutan
# ═══════════════════════════════════════════════════════════════════
class TestCatalogSorting(PostgresCatalogTestCase):
    """Memastikan aturan sortir konsisten pada data database."""

    def test_sort_price_ascending(self):
        """Sortir price_asc mengurutkan harga dari termurah ke termahal"""
        self.assertEqual(
            self.ids("sort_by=price_asc&per_page=100"),
            ["pgt-005", "pgt-006", "pgt-001", "pgt-002", "pgt-007", "pgt-003", "pgt-004"],
        )

    def test_sort_price_descending(self):
        """Sortir price_desc mengurutkan harga dari termahal ke termurah"""
        self.assertEqual(
            self.ids("sort_by=price_desc&per_page=100"),
            ["pgt-004", "pgt-003", "pgt-007", "pgt-002", "pgt-001", "pgt-006", "pgt-005"],
        )

    def test_sort_by_name(self):
        """Sortir name mengurutkan nama produk secara alfabetis"""
        self.assertEqual(
            self.ids("sort_by=name&per_page=100"),
            ["pgt-001", "pgt-002", "pgt-003", "pgt-004", "pgt-007", "pgt-005", "pgt-006"],
        )

    def test_sort_by_score_descending(self):
        """Sortir score mengurutkan rata-rata skor dari tertinggi"""
        self.assertEqual(
            self.ids("sort_by=score&per_page=100"),
            ["pgt-004", "pgt-001", "pgt-003", "pgt-006", "pgt-002", "pgt-007", "pgt-005"],
        )

    def test_default_sort_is_score(self):
        """Tanpa sort_by, urutan default adalah skor tertinggi lebih dulu"""
        self.assertEqual(self.ids("per_page=100")[:2], ["pgt-004", "pgt-001"])

    def test_invalid_sort_returns_422(self):
        """Nilai sort_by tidak dikenal ditolak dengan HTTP 422"""
        self.assertEqual(self.get("sort_by=unknown").status_code, 422)


# ═══════════════════════════════════════════════════════════════════
# Test Suite 5 — Paginasi
# ═══════════════════════════════════════════════════════════════════
class TestCatalogPagination(PostgresCatalogTestCase):
    """Memastikan metadata dan irisan paginasi akurat terhadap data database."""

    def test_pagination_metadata_and_size(self):
        """Metadata total, page, per_page dan jumlah item paginasi akurat"""
        data = self.get("page=1&per_page=3&sort_by=price_asc").json()
        self.assertEqual(len(data["products"]), 3)
        self.assertEqual((data["total"], data["page"], data["per_page"]), (7, 1, 3))

    def test_pages_cover_all_rows_without_overlap(self):
        """Halaman 1-3 (per_page=3) memuat 3+3+1 produk, tanpa duplikat dan tanpa yang terlewat"""
        pages = [self.ids(f"page={n}&per_page=3&sort_by=price_asc") for n in (1, 2, 3)]
        self.assertEqual([len(p) for p in pages], [3, 3, 1])
        flat = [pid for page in pages for pid in page]
        self.assertEqual(len(flat), len(set(flat)))
        self.assertEqual(sorted(flat), sorted(ACTIVE_IDS))

    def test_page_beyond_range_returns_empty_list(self):
        """Halaman di luar jangkauan mengembalikan daftar kosong dengan total tetap 7"""
        data = self.get("page=99&per_page=5").json()
        self.assertEqual(data["products"], [])
        self.assertEqual(data["total"], 7)

    def test_per_page_upper_limit_accepted(self):
        """per_page=100 (batas atas) diterima dan mengembalikan seluruh 7 produk"""
        data = self.get("per_page=100").json()
        self.assertEqual(len(data["products"]), 7)
        self.assertEqual(data["per_page"], 100)

    def test_invalid_pagination_params_return_422(self):
        """Parameter page/per_page di luar batas ditolak dengan HTTP 422"""
        self.assertEqual(self.get("page=0").status_code, 422)
        self.assertEqual(self.get("per_page=0").status_code, 422)
        self.assertEqual(self.get("per_page=101").status_code, 422)


# ═══════════════════════════════════════════════════════════════════
# Test Suite 6 — Konsistensi Data Produk dari Database
# ═══════════════════════════════════════════════════════════════════
class TestCatalogDataConsistency(PostgresCatalogTestCase):
    """Atribut produk di respons harus sama dengan baris tabel yang dimasukkan."""

    def test_response_fields_match_database_rows(self):
        """Seluruh atribut tiap produk (brand, kategori, harga, tags, garansi, specs) sesuai baris DB"""
        items = {p["id"]: p for p in self.get("per_page=100").json()["products"]}
        for spec in FIXTURES:
            if not spec.get("is_active", True):
                continue
            item = items[spec["id"]]
            self.assertEqual(item["name"], spec["name"])
            self.assertEqual(item["brand"], spec["brand"])
            self.assertEqual(item["category"], spec["category"])
            self.assertEqual(item["price"], spec["price"])
            self.assertEqual(sorted(item["tags"]), sorted(spec["tags"]))
            self.assertEqual(item["warranty"]["coverage"], "Garansi resmi - hardware")
            self.assertEqual(item["specs"]["display"], f"Layar {spec['name']}")
            self.assertEqual(item["review_sentiment"]["pros"], [f"Kelebihan {spec['name']}"])

    def test_product_detail_reads_from_database(self):
        """Endpoint detail /api/products/{id} juga membaca database; ID memori tidak terpengaruh"""
        res = client.get("/api/products/pgt-003")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["name"], "Beta Book Air")

    def test_tws_category_filter_reads_database(self):
        """Filter category=tws mengembalikan baris tws dari database (pgt-005)"""
        self.assertEqual(self.ids("category=tws"), ["pgt-005"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
