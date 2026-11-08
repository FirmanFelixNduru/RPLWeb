"""
CompareBuy — Trusted Client IP Resolution (SEC-008 Phase 2: W2)
Resolves verified client IP address for Render production deployment and local development.
"""
from __future__ import annotations

import ipaddress
import os
from typing import Any, Mapping

from starlette.requests import Request


class ClientIPResolutionError(Exception):
    """Raised when client IP cannot be securely resolved from trusted sources."""
    pass


def is_render_runtime() -> bool:
    """Return True if running in the Render production environment."""
    return os.getenv("RENDER", "").strip().lower() == "true"


def resolve_client_ip(request: Request | Mapping[str, Any]) -> str:
    """Resolve and return canonical client IP address.

    Contract:
    - In Render production (`RENDER=true`):
      Reads exclusively from `CF-Connecting-IP` (overwritten by Cloudflare/Render ingress).
      Never falls back to `X-Forwarded-For`, `X-Real-IP`, or peer connection host.
      Rejects missing, duplicate, comma-separated, port-containing, zone-containing,
      or malformed headers.
    - In local development (`RENDER != "true"`):
      Reads exclusively from ASGI direct peer connection (`client.host`).
      Ignores all forwarded headers (including spoofed `CF-Connecting-IP`).
      Rejects missing or invalid peer addresses.

    Returns:
        Canonical IP address string (e.g. '203.0.113.195' or '2001:db8::1').

    Raises:
        ClientIPResolutionError: If client IP cannot be securely resolved.
    """
    if is_render_runtime():
        return _resolve_render_client_ip(request)
    return _resolve_local_client_ip(request)


def _get_raw_headers(request: Request | Mapping[str, Any]) -> list[tuple[bytes, bytes]]:
    """Extract raw header tuples from Starlette Request or ASGI scope."""
    if isinstance(request, Request):
        scope = request.scope
    elif isinstance(request, Mapping):
        scope = request
    else:
        raise ClientIPResolutionError("Invalid request object for IP resolution")

    return list(scope.get("headers", []))


def _resolve_render_client_ip(request: Request | Mapping[str, Any]) -> str:
    """Resolve client IP from CF-Connecting-IP on Render."""
    raw_headers = _get_raw_headers(request)

    # Case-insensitive lookup of all CF-Connecting-IP headers
    cf_values: list[str] = []
    for k, v in raw_headers:
        if k.lower() == b"cf-connecting-ip":
            try:
                cf_values.append(v.decode("latin-1").strip())
            except Exception:
                raise ClientIPResolutionError("Malformed CF-Connecting-IP encoding")

    if not cf_values:
        raise ClientIPResolutionError("Missing CF-Connecting-IP header on Render")

    if len(cf_values) > 1:
        raise ClientIPResolutionError("Duplicate CF-Connecting-IP header detected")

    raw_ip = cf_values[0]
    if not raw_ip:
        raise ClientIPResolutionError("Empty CF-Connecting-IP header")

    # Reject multi-value / comma-separated lists
    if "," in raw_ip:
        raise ClientIPResolutionError("Multi-value CF-Connecting-IP rejected")

    # Reject port specifiers and IPv6 zone identifiers
    if "%" in raw_ip or "[" in raw_ip or "]" in raw_ip:
        raise ClientIPResolutionError("Invalid IP format (port or zone identifier)")

    try:
        ip_obj = ipaddress.ip_address(raw_ip)
    except ValueError:
        raise ClientIPResolutionError("Invalid CF-Connecting-IP address format")

    return str(ip_obj)


def _resolve_local_client_ip(request: Request | Mapping[str, Any]) -> str:
    """Resolve direct peer connection IP in local development."""
    if isinstance(request, Request):
        client = request.client
        peer_host = client.host if client else None
    elif isinstance(request, Mapping):
        client = request.get("client")
        peer_host = client[0] if (client and len(client) > 0) else None
    else:
        raise ClientIPResolutionError("Invalid request object for IP resolution")

    if not peer_host or not str(peer_host).strip():
        raise ClientIPResolutionError("Direct client peer connection unavailable")

    raw_ip = str(peer_host).strip()

    if "%" in raw_ip or "[" in raw_ip or "]" in raw_ip:
        raise ClientIPResolutionError("Invalid peer IP format (port or zone identifier)")

    try:
        ip_obj = ipaddress.ip_address(raw_ip)
    except ValueError:
        raise ClientIPResolutionError("Invalid peer IP address format")

    return str(ip_obj)
