"""
CompareBuy — Fail-Closed Backend & Database Health Verification Tests
Validates PR #4 backend fail-closed behavior, health check semantics, and secret safety.
Tests A through J covering all acceptance criteria.
"""
import os
import unittest
import logging
from unittest.mock import patch, MagicMock

from fastapi import HTTPException
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

            res_compare = self.client.post("/api/compare", json={"product_ids": ["sm-001", "sm-002"]})
            self.assertEqual(res_compare.status_code, 503)
            self.assertEqual(res_compare.json()["detail"], "Database service unavailable")

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

            res_compare = self.client.post("/api/compare", json={"product_ids": ["sm-001", "sm-002"]})
            self.assertEqual(res_compare.status_code, 503)

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

            # 5. compare
            res5 = self.client.post("/api/compare", json={"product_ids": ["sm-001", "sm-002"]})
            self.assertEqual(res5.status_code, 503)
            self.assertEqual(res5.json()["detail"], "Database service unavailable")

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

            res_compare = self.client.post("/api/compare", json={"product_ids": ["sm-001", "sm-002"]})
            self.assertEqual(res_compare.status_code, 200)
            self.assertEqual(len(res_compare.json()["products"]), 2)

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

    # ─────────────────────────────────────────────────────────────
    # Test K — Session maker call exception in production fails closed
    # ─────────────────────────────────────────────────────────────
    def test_k_sessionmaker_call_exception_in_production(self):
        """When SessionLocal() raises an exception in production, return HTTP 503 without leaking secrets."""
        sensitive_pass = "super_secret_session_pass_789"
        sensitive_url = f"postgresql://user:{sensitive_pass}@supabase.co:5432/db"
        bad_sessionmaker = MagicMock(
            side_effect=OperationalError(sensitive_url, {}, Exception("Pool checkout failure"))
        )
        prod_env = {"APP_ENV": "production", "ALLOW_CATALOG_FALLBACK": "false"}

        with patch.dict(os.environ, prod_env, clear=False), \
             patch.object(db_module, "SessionLocal", bad_sessionmaker), \
             patch.object(db_module, "engine", MagicMock()), \
             self.assertLogs("app.db", level="ERROR") as cm:

            # 1. Direct get_db dependency check
            gen = get_db()
            with self.assertRaises(HTTPException) as ctx:
                next(gen)
            self.assertEqual(ctx.exception.status_code, 503)
            self.assertEqual(ctx.exception.detail, "Database service unavailable")
            self.assertNotIn(sensitive_pass, str(ctx.exception.detail))

            # 2. Endpoint integration check
            res = self.client.get("/api/products")
            self.assertEqual(res.status_code, 503)
            self.assertEqual(res.json(), {"detail": "Database service unavailable"})
            self.assertNotIn(sensitive_pass, res.text)

            # 3. Log redaction check
            for log_msg in cm.output:
                self.assertNotIn(sensitive_pass, log_msg)

    # ─────────────────────────────────────────────────────────────
    # Test L — Session maker call exception in development permits fallback
    # ─────────────────────────────────────────────────────────────
    def test_l_sessionmaker_call_exception_in_development_fallback(self):
        """When SessionLocal() raises in development with fallback allowed, yields None and serves catalog."""
        bad_sessionmaker = MagicMock(side_effect=OperationalError("connection failed", {}, Exception("down")))
        dev_env = {"APP_ENV": "development", "ALLOW_CATALOG_FALLBACK": "true"}

        with patch.dict(os.environ, dev_env, clear=False), \
             patch.object(db_module, "SessionLocal", bad_sessionmaker), \
             patch.object(db_module, "engine", MagicMock()):

            # 1. Direct get_db dependency yields None
            gen = get_db()
            session = next(gen)
            self.assertIsNone(session)

            # 2. Catalog endpoint gracefully falls back to in-memory catalogue
            res = self.client.get("/api/products")
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertGreater(data["total"], 0)

    # ─────────────────────────────────────────────────────────────
    # Test M — Session lifecycle: close in finally and unmasked endpoint exceptions
    # ─────────────────────────────────────────────────────────────
    def test_m_successful_session_closed_and_endpoint_exception_not_masked(self):
        """Successfully instantiated session is closed in finally; endpoint exceptions are not swallowed."""
        mock_session = MagicMock()
        good_sessionmaker = MagicMock(return_value=mock_session)

        with patch.object(db_module, "SessionLocal", good_sessionmaker), \
             patch.object(db_module, "engine", MagicMock()):

            # 1. Normal completion closes session
            gen = get_db()
            session = next(gen)
            self.assertEqual(session, mock_session)
            mock_session.close.assert_not_called()
            try:
                next(gen)
            except StopIteration:
                pass
            mock_session.close.assert_called_once()

            # 2. Endpoint exception does not get caught/swallowed, but session still closes
            mock_session.reset_mock()
            gen2 = get_db()
            session2 = next(gen2)
            self.assertEqual(session2, mock_session)
            with self.assertRaises(ValueError) as err_ctx:
                gen2.throw(ValueError("Specific domain error in router"))
            self.assertEqual(str(err_ctx.exception), "Specific domain error in router")
            mock_session.close.assert_called_once()

    # ─────────────────────────────────────────────────────────────
    # Test N — Docker HEALTHCHECK probe logic
    # ─────────────────────────────────────────────────────────────
    def test_n_docker_healthcheck_probe_logic(self):
        """Docker HEALTHCHECK probe logic raises_for_status on HTTP 503 and passes on HTTP 200."""
        import httpx

        # Simulating HTTP 200 response
        mock_resp_200 = httpx.Response(
            status_code=200,
            json={"status": "ok", "database": "connected"},
            request=httpx.Request("GET", "http://localhost:8000/health")
        )
        with patch("httpx.get", return_value=mock_resp_200):
            resp = httpx.get("http://localhost:8000/health", timeout=5.0)
            # Should not raise
            resp.raise_for_status()
            self.assertEqual(resp.status_code, 200)

        # Simulating HTTP 503 response
        mock_resp_503 = httpx.Response(
            status_code=503,
            json={"status": "unavailable", "database": "disconnected"},
            request=httpx.Request("GET", "http://localhost:8000/health")
        )
        with patch("httpx.get", return_value=mock_resp_503):
            resp = httpx.get("http://localhost:8000/health", timeout=5.0)
            with self.assertRaises(httpx.HTTPStatusError) as status_err:
                resp.raise_for_status()
            self.assertEqual(status_err.exception.response.status_code, 503)


if __name__ == "__main__":
    unittest.main()
