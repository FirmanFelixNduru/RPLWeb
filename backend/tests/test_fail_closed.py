"""
CompareBuy — Fail-Closed Backend & Database Health Verification Tests
Validates PR #4 backend fail-closed behavior, health check semantics, and secret safety.
Tests A through J covering all acceptance criteria.
"""
import os
import unittest
import logging
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError

from app.main import app
from app.db import (
    get_db,
    is_db_connected,
    is_fallback_allowed,
    is_production_mode,
    get_app_env,
    get_database_status,
    DatabaseStatus,
    scrub_db_secrets,
)
import app.db as db_module
from app.repositories import catalog_repo
import app.products as products_module


class TestBackendFailClosed(unittest.TestCase):
    """Test suite verifying fail-closed database policy across production and dev modes."""

    def setUp(self):
        self.client = TestClient(app)
        app.dependency_overrides.clear()

    def tearDown(self):
        app.dependency_overrides.clear()

    # ─────────────────────────────────────────────────────────────
    # Test A — Database available
    # ─────────────────────────────────────────────────────────────
    def test_a_database_available(self):
        """When database is live, /health returns 200 and get_db yields active session."""
        test_engine = create_engine("sqlite:///:memory:")
        test_sessionmaker = sessionmaker(bind=test_engine)

        with patch.object(db_module, "engine", test_engine), \
             patch.object(db_module, "SessionLocal", test_sessionmaker), \
             patch.object(db_module, "DATABASE_URL", "sqlite:///:memory:"):

            self.assertTrue(is_db_connected())
            self.assertEqual(get_database_status(), DatabaseStatus.CONNECTED)

            # Test get_db dependency yields a live session
            gen = get_db()
            session = next(gen)
            self.assertIsNotNone(session)
            # Verify close upon finally
            try:
                next(gen)
            except StopIteration:
                pass

            # Test /health endpoint returns 200 with connected status
            res = self.client.get("/health")
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.json(), {"status": "ok", "database": "connected"})

    # ─────────────────────────────────────────────────────────────
    # Test B — Database URL missing in production
    # ─────────────────────────────────────────────────────────────
    def test_b_database_url_missing_production(self):
        """In production without DATABASE_URL, health returns 503 and catalog endpoints fail-closed."""
        prod_env = {
            "APP_ENV": "production",
            "RENDER": "",
            "DATABASE_URL": "",
            "ALLOW_CATALOG_FALLBACK": "false",
        }

        with patch.dict(os.environ, prod_env, clear=False), \
             patch.object(db_module, "DATABASE_URL", None), \
             patch.object(db_module, "engine", None), \
             patch.object(db_module, "SessionLocal", None):

            self.assertTrue(is_production_mode())
            self.assertFalse(is_fallback_allowed())
            self.assertEqual(get_database_status(), DatabaseStatus.UNCONFIGURED)
            self.assertFalse(is_db_connected())

            # Health readiness check fails with 503
            res_health = self.client.get("/health")
            self.assertEqual(res_health.status_code, 503)
            self.assertEqual(res_health.json(), {"status": "unavailable", "database": "disconnected"})

            # Catalog endpoints must return 503 without falling back to memory
            res_products = self.client.get("/api/products")
            self.assertEqual(res_products.status_code, 503)
            self.assertEqual(res_products.json()["detail"], "Database service unavailable")

            res_detail = self.client.get("/api/products/sm-001")
            self.assertEqual(res_detail.status_code, 503)
            self.assertEqual(res_detail.json()["detail"], "Database service unavailable")

            res_brands = self.client.get("/api/brands")
            self.assertEqual(res_brands.status_code, 503)

            res_tags = self.client.get("/api/tags")
            self.assertEqual(res_tags.status_code, 503)

    # ─────────────────────────────────────────────────────────────
    # Test C — Engine initialization failure
    # ─────────────────────────────────────────────────────────────
    def test_c_engine_initialization_failure(self):
        """When engine fails to initialize in production, health is 503 and catalog is 503."""
        prod_env = {"APP_ENV": "production", "ALLOW_CATALOG_FALLBACK": "false"}

        with patch.dict(os.environ, prod_env, clear=False), \
             patch.object(db_module, "DATABASE_URL", "postgresql+psycopg2://user:pass@localhost:5432/bad_db"), \
             patch.object(db_module, "engine", None), \
             patch.object(db_module, "SessionLocal", None):

            self.assertEqual(get_database_status(), DatabaseStatus.INIT_FAILED)
            self.assertFalse(is_db_connected())

            res_health = self.client.get("/health")
            self.assertEqual(res_health.status_code, 503)
            self.assertEqual(res_health.json(), {"status": "unavailable", "database": "disconnected"})

            res_catalog = self.client.get("/api/products")
            self.assertEqual(res_catalog.status_code, 503)

    # ─────────────────────────────────────────────────────────────
    # Test D — Runtime connection failure (SELECT 1 fails)
    # ─────────────────────────────────────────────────────────────
    def test_d_runtime_connection_failure(self):
        """When engine exists but SELECT 1 fails at runtime, health returns 503 without leaking details."""
        mock_engine = MagicMock()
        mock_engine.connect.side_effect = OperationalError("SELECT 1", {}, Exception("Connection refused to internal:5432"))

        prod_env = {"APP_ENV": "production", "ALLOW_CATALOG_FALLBACK": "false"}

        with patch.dict(os.environ, prod_env, clear=False), \
             patch.object(db_module, "DATABASE_URL", "postgresql+psycopg2://user:pass@localhost:5432/db"), \
             patch.object(db_module, "engine", mock_engine), \
             patch.object(db_module, "SessionLocal", MagicMock()):

            self.assertEqual(get_database_status(), DatabaseStatus.DISCONNECTED)
            self.assertFalse(is_db_connected())

            res = self.client.get("/health")
            self.assertEqual(res.status_code, 503)
            self.assertEqual(res.json(), {"status": "unavailable", "database": "disconnected"})
            # Verify no secret or internal details in body
            self.assertNotIn("Connection refused", res.text)
            self.assertNotIn("5432", res.text)

    # ─────────────────────────────────────────────────────────────
    # Test E — Catalog query failure in production
    # ─────────────────────────────────────────────────────────────
    def test_e_catalog_query_failure(self):
        """When a database query raises an exception during request execution in production, return 503."""
        mock_db = MagicMock()

        app.dependency_overrides[get_db] = lambda: mock_db
        prod_env = {"APP_ENV": "production", "ALLOW_CATALOG_FALLBACK": "false"}

        with patch.dict(os.environ, prod_env, clear=False), \
             patch.object(catalog_repo, "get_catalog_products", side_effect=OperationalError("query", {}, Exception("DB timeout"))), \
             patch.object(catalog_repo, "get_product_by_id", side_effect=OperationalError("query", {}, Exception("DB timeout"))), \
             patch.object(catalog_repo, "get_all_brands", side_effect=OperationalError("query", {}, Exception("DB timeout"))), \
             patch.object(catalog_repo, "get_all_tags", side_effect=OperationalError("query", {}, Exception("DB timeout"))), \
             patch.object(products_module, "get_all_products") as mock_fallback_products:

            # 1. list_products
            res1 = self.client.get("/api/products")
            self.assertEqual(res1.status_code, 503)
            mock_fallback_products.assert_not_called()

            # 2. get_product
            res2 = self.client.get("/api/products/sm-001")
            self.assertEqual(res2.status_code, 503)

            # 3. brands
            res3 = self.client.get("/api/brands")
            self.assertEqual(res3.status_code, 503)

            # 4. tags
            res4 = self.client.get("/api/tags")
            self.assertEqual(res4.status_code, 503)

    # ─────────────────────────────────────────────────────────────
    # Test F — Empty database (zero products)
    # ─────────────────────────────────────────────────────────────
    def test_f_empty_database_returns_empty_contract(self):
        """When database is available but contains 0 products, return empty list without falling back."""
        mock_db = MagicMock()
        app.dependency_overrides[get_db] = lambda: mock_db

        with patch.object(catalog_repo, "get_catalog_products", return_value=([], 0)), \
             patch.object(products_module, "get_all_products") as mock_fallback:

            res = self.client.get("/api/products")
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertEqual(data["products"], [])
            self.assertEqual(data["total"], 0)
            self.assertEqual(data["page"], 1)
            self.assertEqual(data["per_page"], 20)

            # In-memory catalogue must NEVER be called
            mock_fallback.assert_not_called()

    # ─────────────────────────────────────────────────────────────
    # Test G — Product not found in database
    # ─────────────────────────────────────────────────────────────
    def test_g_product_not_found_returns_404(self):
        """When product is not found in database, production returns 404 without checking in-memory."""
        mock_db = MagicMock()
        app.dependency_overrides[get_db] = lambda: mock_db

        prod_env = {"APP_ENV": "production", "ALLOW_CATALOG_FALLBACK": "false"}

        with patch.dict(os.environ, prod_env, clear=False), \
             patch.object(catalog_repo, "get_product_by_id", return_value=None), \
             patch.object(products_module, "get_product_by_id") as mock_fallback_product:

            res = self.client.get("/api/products/nonexistent-id-12345")
            self.assertEqual(res.status_code, 404)
            self.assertEqual(res.json()["detail"], "Product not found")

            # Must NOT check in-memory fallback
            mock_fallback_product.assert_not_called()

    # ─────────────────────────────────────────────────────────────
    # Test H — Development fallback when explicitly permitted
    # ─────────────────────────────────────────────────────────────
    def test_h_development_fallback_when_explicitly_permitted(self):
        """In development with ALLOW_CATALOG_FALLBACK=true, catalog falls back smoothly to in-memory."""
        dev_env = {
            "APP_ENV": "development",
            "ALLOW_CATALOG_FALLBACK": "true",
            "RENDER": "",
        }

        with patch.dict(os.environ, dev_env, clear=False), \
             patch.object(db_module, "SessionLocal", None), \
             patch.object(db_module, "engine", None):

            self.assertFalse(is_production_mode())
            self.assertTrue(is_fallback_allowed())

            # Health reports degraded / fallback enabled
            res_health = self.client.get("/health")
            self.assertEqual(res_health.status_code, 200)
            self.assertEqual(res_health.json()["status"], "degraded")
            self.assertEqual(res_health.json()["fallback"], "enabled")

            # Catalog endpoints fall back to memory
            res_products = self.client.get("/api/products")
            self.assertEqual(res_products.status_code, 200)
            self.assertGreaterEqual(res_products.json()["total"], 15)

            res_detail = self.client.get("/api/products/sm-001")
            self.assertEqual(res_detail.status_code, 200)
            self.assertEqual(res_detail.json()["id"], "sm-001")

            res_brands = self.client.get("/api/brands")
            self.assertEqual(res_brands.status_code, 200)
            self.assertIn("brands", res_brands.json())

            res_tags = self.client.get("/api/tags")
            self.assertEqual(res_tags.status_code, 200)
            self.assertIn("tags", res_tags.json())

    # ─────────────────────────────────────────────────────────────
    # Test I — Testing compatibility and dependency injection
    # ─────────────────────────────────────────────────────────────
    def test_i_testing_compatibility_and_dependency_injection(self):
        """Test harness overrides and fixtures function without real Supabase connection."""
        test_engine = create_engine("sqlite:///:memory:")
        test_sessionmaker = sessionmaker(bind=test_engine)

        def override_db():
            session = test_sessionmaker()
            try:
                yield session
            finally:
                session.close()

        app.dependency_overrides[get_db] = override_db

        with patch.object(catalog_repo, "get_all_brands", return_value=["MockBrandA", "MockBrandB"]):
            res = self.client.get("/api/brands")
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.json()["brands"], ["MockBrandA", "MockBrandB"])

        app.dependency_overrides.clear()

    # ─────────────────────────────────────────────────────────────
    # Test J — Secret safety in responses and logging
    # ─────────────────────────────────────────────────────────────
    def test_j_secret_safety_in_responses_and_logging(self):
        """Database connection strings and passwords must never appear in responses or logs."""
        sensitive_url = "postgresql+psycopg2://postgres:super_secret_password_xyz987@db.supabase.co:5432/postgres"

        # 1. Verify scrub_db_secrets
        scrubbed = scrub_db_secrets(sensitive_url)
        self.assertNotIn("super_secret_password_xyz987", scrubbed)
        self.assertIn("postgres:***@", scrubbed)

        # 2. Verify HTTP error response does not contain password or connection string
        mock_db = MagicMock()
        app.dependency_overrides[get_db] = lambda: mock_db
        prod_env = {"APP_ENV": "production", "ALLOW_CATALOG_FALLBACK": "false"}

        with patch.dict(os.environ, prod_env, clear=False), \
             patch.object(catalog_repo, "get_catalog_products", side_effect=OperationalError(sensitive_url, {}, Exception("Failed"))), \
             self.assertLogs("app.routers.catalog", level="ERROR") as cm:

            res = self.client.get("/api/products")
            self.assertEqual(res.status_code, 503)

            # Response body check
            self.assertNotIn("super_secret_password_xyz987", res.text)
            self.assertNotIn("supabase.co", res.text)
            self.assertEqual(res.json(), {"detail": "Database service unavailable"})

            # Log messages check
            for log_msg in cm.output:
                self.assertNotIn("super_secret_password_xyz987", log_msg)


if __name__ == "__main__":
    unittest.main()
