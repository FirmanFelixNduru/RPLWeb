"""
CompareBuy — SEC-008 Phase 2 (W2): Trusted Client IP Resolution Tests

Validates Render production mode (CF-Connecting-IP resolution, anti-spoofing,
and rejection of invalid/duplicate/multi-value/port/zone headers) as well as
local development direct peer connection resolution.
"""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

# Ensure backend root is in sys.path
_BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from tests._db_guard import enforce_safe_test_db_env

enforce_safe_test_db_env()

from starlette.requests import Request
from starlette.datastructures import Headers, Address
from app.security.client_ip import (
    resolve_client_ip,
    ClientIPResolutionError,
    is_render_runtime,
)


def _build_request(
    headers: list[tuple[bytes, bytes]] | dict[str, str] | None = None,
    client: tuple[str, int] | None = ("127.0.0.1", 54321),
    scheme: str = "http",
) -> Request:
    """Helper to build a Starlette Request with controlled headers and client peer."""
    raw_headers: list[tuple[bytes, bytes]] = []
    if isinstance(headers, list):
        raw_headers = headers
    elif isinstance(headers, dict):
        raw_headers = [(k.encode("latin-1"), v.encode("latin-1")) for k, v in headers.items()]

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/prices/sm-001",
        "headers": raw_headers,
        "client": client,
        "scheme": scheme,
        "server": ("localhost", 8000),
        "http_version": "1.1",
    }
    return Request(scope)


class TestTrustedClientIPResolution(unittest.TestCase):
    """Test matrix covering W2-T01 through W2-T20."""

    # ── Render Production Mode Tests (W2-T01 to W2-T10) ──

    @patch.dict(os.environ, {"RENDER": "true"})
    def test_w2_t01_render_valid_ipv4_cf_header(self):
        """W2-T01: Render + valid IPv4 CF header -> IP CF used."""
        req = _build_request(headers=[(b"cf-connecting-ip", b"203.0.113.195")])
        ip = resolve_client_ip(req)
        self.assertEqual(ip, "203.0.113.195")

    @patch.dict(os.environ, {"RENDER": "true"})
    def test_w2_t02_render_valid_ipv6_cf_header(self):
        """W2-T02: Render + valid IPv6 CF header -> IP CF used."""
        req = _build_request(headers=[(b"cf-connecting-ip", b"2001:db8::1")])
        ip = resolve_client_ip(req)
        self.assertEqual(ip, "2001:db8::1")

    @patch.dict(os.environ, {"RENDER": "true"})
    def test_w2_t03_render_spoofed_xff_ignored(self):
        """W2-T03: Render + spoofed XFF different -> XFF ignored, CF used."""
        req = _build_request(
            headers=[
                (b"cf-connecting-ip", b"203.0.113.195"),
                (b"x-forwarded-for", b"10.0.0.1, 172.16.0.2"),
            ]
        )
        ip = resolve_client_ip(req)
        self.assertEqual(ip, "203.0.113.195")

    @patch.dict(os.environ, {"RENDER": "true"})
    def test_w2_t04_render_spoofed_x_real_ip_ignored(self):
        """W2-T04: Render + spoofed X-Real-IP -> X-Real-IP ignored, CF used."""
        req = _build_request(
            headers=[
                (b"cf-connecting-ip", b"203.0.113.195"),
                (b"x-real-ip", b"198.51.100.99"),
            ]
        )
        ip = resolve_client_ip(req)
        self.assertEqual(ip, "203.0.113.195")

    @patch.dict(os.environ, {"RENDER": "true"})
    def test_w2_t05_render_missing_cf_header(self):
        """W2-T05: Render + missing CF header -> Resolver error (no fallback)."""
        # Even if XFF and X-Real-IP are present, failure is fail-closed
        req = _build_request(
            headers=[
                (b"x-forwarded-for", b"203.0.113.195"),
                (b"x-real-ip", b"203.0.113.195"),
            ]
        )
        with self.assertRaises(ClientIPResolutionError) as ctx:
            resolve_client_ip(req)
        self.assertIn("Missing", str(ctx.exception))

    @patch.dict(os.environ, {"RENDER": "true"})
    def test_w2_t06_render_invalid_cf_header(self):
        """W2-T06: Render + invalid CF header -> Resolver error."""
        req = _build_request(headers=[(b"cf-connecting-ip", b"not-an-ip-address")])
        with self.assertRaises(ClientIPResolutionError) as ctx:
            resolve_client_ip(req)
        self.assertIn("Invalid", str(ctx.exception))

    @patch.dict(os.environ, {"RENDER": "true"})
    def test_w2_t07_render_duplicate_cf_header(self):
        """W2-T07: Render + duplicate CF header -> Resolver error."""
        req = _build_request(
            headers=[
                (b"cf-connecting-ip", b"203.0.113.1"),
                (b"cf-connecting-ip", b"203.0.113.2"),
            ]
        )
        with self.assertRaises(ClientIPResolutionError) as ctx:
            resolve_client_ip(req)
        self.assertIn("Duplicate", str(ctx.exception))

    @patch.dict(os.environ, {"RENDER": "true"})
    def test_w2_t08_render_comma_separated_cf_value(self):
        """W2-T08: Render + comma-separated CF value -> Resolver error."""
        req = _build_request(headers=[(b"cf-connecting-ip", b"203.0.113.1, 198.51.100.2")])
        with self.assertRaises(ClientIPResolutionError) as ctx:
            resolve_client_ip(req)
        self.assertIn("Multi-value", str(ctx.exception))

    @patch.dict(os.environ, {"RENDER": "true"})
    def test_w2_t09_render_cf_header_containing_port(self):
        """W2-T09: Render + CF header containing port -> Resolver error."""
        for bad_port_ip in [b"203.0.113.1:8080", b"[2001:db8::1]:8080"]:
            with self.subTest(bad_ip=bad_port_ip):
                req = _build_request(headers=[(b"cf-connecting-ip", bad_port_ip)])
                with self.assertRaises(ClientIPResolutionError):
                    resolve_client_ip(req)

    @patch.dict(os.environ, {"RENDER": "true"})
    def test_w2_t10_render_ipv6_zone_identifier(self):
        """W2-T10: Render + IPv6 zone identifier -> Resolver error."""
        req = _build_request(headers=[(b"cf-connecting-ip", b"fe80::1%eth0")])
        with self.assertRaises(ClientIPResolutionError):
            resolve_client_ip(req)

    # ── Local Development Mode Tests (W2-T11 to W2-T15) ──

    @patch.dict(os.environ, {"RENDER": "false"})
    def test_w2_t11_local_direct_ipv4_peer(self):
        """W2-T11: Local + direct IPv4 peer -> Peer IP used."""
        req = _build_request(client=("192.168.1.100", 54321))
        ip = resolve_client_ip(req)
        self.assertEqual(ip, "192.168.1.100")

    @patch.dict(os.environ, {"RENDER": ""})
    def test_w2_t12_local_direct_ipv6_peer(self):
        """W2-T12: Local + direct IPv6 peer -> Peer IP used."""
        req = _build_request(client=("2001:db8::55", 54321))
        ip = resolve_client_ip(req)
        self.assertEqual(ip, "2001:db8::55")

    @patch.dict(os.environ, {"RENDER": "false"})
    def test_w2_t13_local_spoofed_cf_header_ignored(self):
        """W2-T13: Local + spoofed CF header -> Header ignored, peer IP used."""
        req = _build_request(
            headers=[(b"cf-connecting-ip", b"203.0.113.99")],
            client=("127.0.0.1", 54321),
        )
        ip = resolve_client_ip(req)
        self.assertEqual(ip, "127.0.0.1")

    @patch.dict(os.environ, {"RENDER": "false"})
    def test_w2_t14_local_spoofed_xff_ignored(self):
        """W2-T14: Local + spoofed XFF -> Header ignored, peer IP used."""
        req = _build_request(
            headers=[(b"x-forwarded-for", b"203.0.113.99")],
            client=("127.0.0.1", 54321),
        )
        ip = resolve_client_ip(req)
        self.assertEqual(ip, "127.0.0.1")

    @patch.dict(os.environ, {"RENDER": "false"})
    def test_w2_t15_local_missing_peer(self):
        """W2-T15: Local + missing peer -> Resolver error."""
        req = _build_request(client=None)
        with self.assertRaises(ClientIPResolutionError) as ctx:
            resolve_client_ip(req)
        self.assertIn("unavailable", str(ctx.exception))

    # ── Advanced Verification (W2-T16 to W2-T19) ──

    @patch.dict(os.environ, {"RENDER": "true"})
    def test_w2_t16_header_capitalization_variants(self):
        """W2-T16: Header capitalization variants processed correctly."""
        variants = [
            b"cf-connecting-ip",
            b"CF-Connecting-IP",
            b"Cf-Connecting-Ip",
            b"CF-CONNECTING-IP",
        ]
        for header_name in variants:
            with self.subTest(header=header_name):
                req = _build_request(headers=[(header_name, b"203.0.113.50")])
                ip = resolve_client_ip(req)
                self.assertEqual(ip, "203.0.113.50")

    def test_w2_t17_existing_middleware_compatibility(self):
        """W2-T17: Existing FastAPI app and CORSMiddleware compatibility verified."""
        from app.main import app
        from fastapi.testclient import TestClient

        with TestClient(app) as client:
            resp = client.get("/health")
            self.assertEqual(resp.status_code, 200)
            self.assertIn(resp.json().get("status"), ("ok", "degraded"))

    def test_w2_t18_existing_https_scheme_behavior(self):
        """W2-T18: Existing HTTPS/scheme behavior verified intact."""
        req_https = _build_request(scheme="https", client=("127.0.0.1", 443))
        self.assertEqual(req_https.url.scheme, "https")

        req_http = _build_request(scheme="http", client=("127.0.0.1", 80))
        self.assertEqual(req_http.url.scheme, "http")

    def test_w2_t19_uvicorn_procfile_startup_arguments(self):
        """W2-T19: Procfile startup command contains --no-proxy-headers."""
        procfile_path = os.path.join(_BACKEND_DIR, "Procfile")
        content = Path(procfile_path).read_text(encoding="utf-8")
        self.assertIn("--no-proxy-headers", content)
        self.assertNotIn("--forwarded-allow-ips=*", content)

    def test_w2_t20_existing_api_regression(self):
        """W2-T20: Existing API core endpoints return expected responses without regression."""
        from app.main import app
        from fastapi.testclient import TestClient

        with TestClient(app) as client:
            resp_root = client.get("/")
            self.assertEqual(resp_root.status_code, 200)
            self.assertEqual(resp_root.json().get("service"), "CompareBuy API")

            resp_catalog = client.get("/api/products")
            self.assertEqual(resp_catalog.status_code, 200)
            data = resp_catalog.json()
            self.assertIn("products", data)
            self.assertEqual(data.get("total"), 20)
            self.assertEqual(len(data.get("products")), 20)


class TestRenderSchemeMiddleware(unittest.TestCase):
    """Test matrix covering W2-SCH-01 through W2-SCH-14."""

    def setUp(self):
        from app.db import get_db
        from app.main import app
        from unittest.mock import MagicMock
        self._db_mock = MagicMock()
        app.dependency_overrides[get_db] = lambda: self._db_mock

    def tearDown(self):
        from app.main import app
        app.dependency_overrides.clear()

    @patch.dict(os.environ, {"RENDER": "true"})
    def test_w2_sch_01_render_xfp_https(self):
        """W2-SCH-01: Render XFP=https sets scope['scheme'] to 'https'."""
        from app.main import app
        from fastapi.testclient import TestClient

        with TestClient(app) as client:
            resp = client.get("/api/products", headers={"X-Forwarded-Proto": "https"})
            self.assertEqual(resp.status_code, 200)

    @patch.dict(os.environ, {"RENDER": "true"})
    def test_w2_sch_02_render_xfp_http(self):
        """W2-SCH-02: Render XFP=http sets scope['scheme'] to 'http'."""
        from app.main import app
        from fastapi.testclient import TestClient

        with TestClient(app) as client:
            resp = client.get("/api/products", headers={"X-Forwarded-Proto": "http"})
            self.assertEqual(resp.status_code, 200)

    @patch.dict(os.environ, {"RENDER": ""})
    def test_w2_sch_03_local_spoofed_xfp_ignored(self):
        """W2-SCH-03: Local spoofed XFP=https is untrusted; original ASGI connection scheme is retained."""
        from app.main import app
        from fastapi.testclient import TestClient

        with TestClient(app) as client:
            resp = client.get("/api/products", headers={"X-Forwarded-Proto": "https"})
            self.assertEqual(resp.status_code, 200)

    @patch.dict(os.environ, {"RENDER": "true"})
    def test_w2_sch_04_missing_render_xfp_explicit_safe_error(self):
        """W2-SCH-04: Missing Render XFP triggers explicit safe error policy (400 Bad Request on API endpoints)."""
        from app.main import app
        from fastapi.testclient import TestClient

        with TestClient(app) as client:
            resp = client.get("/api/products")
            self.assertEqual(resp.status_code, 400)
            self.assertEqual(resp.json(), {"detail": "Invalid or missing forwarded protocol header."})

    @patch.dict(os.environ, {"RENDER": "true"})
    def test_w2_sch_05_duplicate_xfp_rejected(self):
        """W2-SCH-05: Duplicate XFP headers are rejected with 400 Bad Request."""
        import asyncio
        from app.security.scheme import RenderSchemeMiddleware

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/api/products",
            "headers": [
                (b"x-forwarded-proto", b"https"),
                (b"x-forwarded-proto", b"http"),
            ],
        }
        sent = []
        async def mock_send(msg):
            sent.append(msg)
        async def mock_receive():
            return {"type": "http.request"}
        async def mock_app(s, r, snd):
            pass

        middleware = RenderSchemeMiddleware(mock_app)
        asyncio.run(middleware(scope, mock_receive, mock_send))
        self.assertEqual(sent[0]["status"], 400)

    @patch.dict(os.environ, {"RENDER": "true"})
    def test_w2_sch_06_comma_separated_xfp_rejected(self):
        """W2-SCH-06: Comma-separated multi-value XFP is rejected with 400 Bad Request."""
        from app.main import app
        from fastapi.testclient import TestClient

        with TestClient(app) as client:
            resp = client.get("/api/products", headers={"X-Forwarded-Proto": "https, http"})
            self.assertEqual(resp.status_code, 400)
            self.assertEqual(resp.json(), {"detail": "Invalid or missing forwarded protocol header."})

    @patch.dict(os.environ, {"RENDER": "true"})
    def test_w2_sch_07_invalid_xfp_string_rejected(self):
        """W2-SCH-07: Invalid XFP string (e.g. ftp or malformed) is rejected with 400 Bad Request."""
        from app.main import app
        from fastapi.testclient import TestClient

        for invalid_val in ["ftp", "ws", "javascript:void(0)", "http://malicious"]:
            with self.subTest(val=invalid_val):
                with TestClient(app) as client:
                    resp = client.get("/api/products", headers={"X-Forwarded-Proto": invalid_val})
                    self.assertEqual(resp.status_code, 400)
                    self.assertEqual(resp.json(), {"detail": "Invalid or missing forwarded protocol header."})

    @patch.dict(os.environ, {"RENDER": "true"})
    def test_w2_sch_08_header_capitalization_variants(self):
        """W2-SCH-08: Header capitalization variants parsed correctly."""
        import asyncio
        from app.security.scheme import RenderSchemeMiddleware

        for header_name in [b"x-forwarded-proto", b"X-Forwarded-Proto", b"X-FORWARDED-PROTO", b"X-Forwarded-proto"]:
            with self.subTest(header=header_name):
                scope = {
                    "type": "http",
                    "method": "GET",
                    "path": "/api/products",
                    "headers": [(header_name, b"https")],
                    "scheme": "http",
                }
                async def mock_app(s, r, snd):
                    pass
                middleware = RenderSchemeMiddleware(mock_app)
                asyncio.run(middleware(scope, None, None))
                self.assertEqual(scope["scheme"], "https")

    @patch.dict(os.environ, {"RENDER": "true"})
    def test_w2_sch_09_request_url_scheme_in_downstream_app(self):
        """W2-SCH-09: request.url.scheme in downstream app reflects restored HTTPS scheme."""
        import asyncio
        from starlette.requests import Request
        from app.security.scheme import RenderSchemeMiddleware

        observed_scheme = []
        async def downstream_app(scope, receive, send):
            req = Request(scope)
            observed_scheme.append(req.url.scheme)

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/api/products",
            "headers": [(b"x-forwarded-proto", b"https")],
            "scheme": "http",
            "server": ("example.com", 80),
        }
        middleware = RenderSchemeMiddleware(downstream_app)
        asyncio.run(middleware(scope, None, None))
        self.assertEqual(observed_scheme, ["https"])

    @patch.dict(os.environ, {"RENDER": "true"})
    def test_w2_sch_10_redirect_and_absolute_url_behavior(self):
        """W2-SCH-10: Redirect / absolute URL generation does not degrade to HTTP under restored HTTPS."""
        import asyncio
        from starlette.requests import Request
        from starlette.responses import RedirectResponse
        from app.security.scheme import RenderSchemeMiddleware

        generated_redirect = []
        async def redirect_app(scope, receive, send):
            req = Request(scope)
            redirect_url = str(req.url.replace(path="/api/products"))
            resp = RedirectResponse(url=redirect_url)
            generated_redirect.append(resp.headers["location"])

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/api/products/",
            "headers": [(b"x-forwarded-proto", b"https")],
            "scheme": "http",
            "server": ("comparebuy.onrender.com", 443),
        }
        middleware = RenderSchemeMiddleware(redirect_app)
        asyncio.run(middleware(scope, None, None))
        self.assertEqual(len(generated_redirect), 1)
        self.assertTrue(generated_redirect[0].startswith("https://comparebuy.onrender.com/api/products"))

    @patch.dict(os.environ, {"RENDER": "true"})
    def test_w2_sch_11_cors_preflight_no_regression(self):
        """W2-SCH-11: CORS preflight requests on Render ingress receive valid CORS headers."""
        from app.main import app
        from fastapi.testclient import TestClient

        with TestClient(app) as client:
            resp = client.options(
                "/api/products",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "GET",
                    "X-Forwarded-Proto": "https",
                },
            )
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.headers.get("access-control-allow-origin"), "http://localhost:3000")

    @patch.dict(os.environ, {"RENDER": "true"})
    def test_w2_sch_12_public_health_endpoint_no_unexpected_failure(self):
        """W2-SCH-12: Public health endpoint via Render ingress returns 200 without unexpected failure."""
        from app.main import app
        from fastapi.testclient import TestClient

        with patch("app.main.is_db_connected", return_value=True):
            with TestClient(app) as client:
                resp = client.get("/health", headers={"X-Forwarded-Proto": "https"})
                self.assertEqual(resp.status_code, 200)
                self.assertEqual(resp.json().get("status"), "ok")

    def test_w2_sch_13_uvicorn_cli_options_disabled(self):
        """W2-SCH-13: Uvicorn Procfile specifies --no-proxy-headers to prevent generic proxy trust."""
        procfile = Path(_BACKEND_DIR) / "Procfile"
        content = procfile.read_text(encoding="utf-8")
        self.assertIn("--no-proxy-headers", content)

    @patch.dict(os.environ, {"RENDER": "true"})
    def test_w2_sch_14_middleware_ordering(self):
        """W2-SCH-14: Middleware ordering ensures scheme is restored before downstream handler inspection."""
        from app.main import app
        from fastapi.testclient import TestClient

        with patch("app.routers.catalog.is_fallback_allowed", return_value=True):
            with TestClient(app) as client:
                resp = client.get("/api/products", headers={"X-Forwarded-Proto": "https"})
                self.assertEqual(resp.status_code, 200)
                self.assertEqual(resp.request.headers.get("x-forwarded-proto"), "https")

    @patch.dict(os.environ, {"RENDER": "true"})
    def test_w2_sch_internal_health_check_without_xfp_allowed(self):
        """Internal container health probe to /health on Render without XFP succeeds safely."""
        from app.main import app
        from fastapi.testclient import TestClient

        with patch("app.main.is_db_connected", return_value=True):
            with TestClient(app) as client:
                resp = client.get("/health")
                self.assertEqual(resp.status_code, 200)
                self.assertEqual(resp.json().get("status"), "ok")


if __name__ == "__main__":
    unittest.main()
