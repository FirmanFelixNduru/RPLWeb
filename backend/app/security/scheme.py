"""
CompareBuy — Render Ingress HTTPS Scheme Preservation Middleware (SEC-008 Phase 2: W2)
Safely restores scope['scheme'] based on verified Render ingress metadata without
enabling Uvicorn generic proxy-header processing.
"""
from __future__ import annotations

import json
import logging
from typing import Callable

from app.security.client_ip import is_render_runtime

logger = logging.getLogger(__name__)


class RenderSchemeMiddleware:
    """Pure ASGI middleware to safely restore scope['scheme'] on Render ingress.

    Under Render, TLS terminates at the Cloudflare / Envoy edge, and traffic is forwarded
    to Uvicorn as plain HTTP. Because `--no-proxy-headers` is passed to Uvicorn to defeat
    wildcard proxy spoofing, Uvicorn does not process `X-Forwarded-Proto`.

    This middleware explicitly inspects `X-Forwarded-Proto` ONLY when `is_render_runtime()`
    is True, validating that exactly one valid header ('http' or 'https') exists.
    In local development (is_render_runtime() is False), forwarded proto headers are untrusted
    and ignored, retaining the underlying ASGI connection scheme.
    """

    def __init__(self, app: Callable):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope.get("type") not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        if not is_render_runtime():
            # Local development: do not trust client-supplied forwarded headers.
            # Preserve connection scheme from underlying ASGI socket.
            await self.app(scope, receive, send)
            return

        # Render production runtime: inspect raw headers for X-Forwarded-Proto
        raw_headers = scope.get("headers", [])
        xfp_headers = [v for k, v in raw_headers if k.lower() == b"x-forwarded-proto"]

        if not xfp_headers:
            # Safe error policy for missing XFP:
            # Allow internal container health checks (/health) to pass with connection scheme.
            if scope.get("path") == "/health":
                await self.app(scope, receive, send)
                return
            # Fail-closed for all other endpoints
            await self._send_error(send, 400, "Invalid or missing forwarded protocol header.")
            return

        if len(xfp_headers) > 1:
            # Duplicate header rejected
            await self._send_error(send, 400, "Invalid or missing forwarded protocol header.")
            return

        raw_val = xfp_headers[0]

        # Reject comma-separated or multi-value
        if b"," in raw_val:
            await self._send_error(send, 400, "Invalid or missing forwarded protocol header.")
            return

        try:
            proto_str = raw_val.decode("ascii").strip().lower()
        except UnicodeDecodeError:
            await self._send_error(send, 400, "Invalid or missing forwarded protocol header.")
            return

        if proto_str not in ("http", "https"):
            # Malformed or unsupported protocol
            await self._send_error(send, 400, "Invalid or missing forwarded protocol header.")
            return

        # Validated: safely update scheme in ASGI scope
        if scope.get("type") == "http":
            scope["scheme"] = proto_str
        elif scope.get("type") == "websocket":
            scope["scheme"] = "wss" if proto_str == "https" else "ws"

        await self.app(scope, receive, send)

    async def _send_error(self, send, status_code: int, message: str):
        body = json.dumps({"detail": message}).encode("utf-8")
        await send({
            "type": "http.response.start",
            "status": status_code,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body)).encode("ascii")),
            ],
        })
        await send({
            "type": "http.response.body",
            "body": body,
        })
