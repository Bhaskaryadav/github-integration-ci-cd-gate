"""
Module 2 — Customer Information MCP Server (stdio)
Lab stub for Module 6 Project 1 validation.

Traffic forwarding:
    Each tool call is forwarded (fire-and-forget) to the banking-api
    dashboard at http://localhost:8080/ingest so it appears on the
    platform-wide MCP Traffic Monitor. If the banking-api server is
    not running, forwarding silently does nothing.

IMPORTANT (stdio transport): never print() in this file — stdout is
the JSON-RPC channel between Claude Code and this server. Any stray
output corrupts the protocol stream.
"""

from __future__ import annotations

import functools
import json
import re
import threading
import time
import urllib.request
from datetime import datetime, timezone
from typing import Any, Callable

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as exc:
    raise SystemExit(
        "Missing dependency: pip install mcp\n"
        f"Original error: {exc}"
    ) from exc

mcp = FastMCP("customer-info")

_CUSTOMERS: dict[str, dict[str, Any]] = {}

_DASHBOARD_INGEST = "http://localhost:8080/ingest"
_PAN_PATTERN = re.compile(r"\b\d{13,19}\b")


def _mask_pci(value: Any) -> Any:
    """Mask anything resembling a card PAN (PCI DSS Req 3) before display."""
    text = json.dumps(value, default=str)
    masked = _PAN_PATTERN.sub(lambda m: f"****{m.group(0)[-4:]}", text)
    return json.loads(masked)


def _forward(event: dict[str, Any]) -> None:
    """POST the event to the dashboard. Silent no-op if it is not running."""
    try:
        req = urllib.request.Request(
            _DASHBOARD_INGEST,
            data=json.dumps(event).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=1.5).close()
    except Exception:
        pass  # dashboard offline — never fail or log on the stdio channel


def monitored(fn: Callable[..., Any]) -> Callable[..., Any]:
    """Forward request/response of an MCP tool to the live dashboard."""

    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        started = time.perf_counter()
        result = fn(*args, **kwargs)
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        event = {
            "ts": datetime.now(timezone.utc).strftime("%H:%M:%S"),
            "server": "customer-info",
            "tool": fn.__name__,
            "request": _mask_pci(kwargs or {}),
            "response": _mask_pci(result),
            "ms": elapsed_ms,
        }
        threading.Thread(target=_forward, args=(event,), daemon=True).start()
        return result

    return wrapper


@mcp.tool()
@monitored
def store_customer_info(
    customer_id: str,
    name: str,
    account_type: str,
    kyc_status: str,
) -> dict[str, Any]:
    """Store a customer profile in the in-memory lab store."""
    record = {
        "customer_id": customer_id,
        "name": name,
        "account_type": account_type,
        "kyc_status": kyc_status,
    }
    _CUSTOMERS[customer_id] = record
    return {"status": "stored", "customer": record}


@mcp.tool()
@monitored
def retrieve_customer_info(customer_id: str) -> dict[str, Any]:
    """Retrieve a customer profile from the in-memory lab store."""
    customer = _CUSTOMERS.get(customer_id)
    if customer is None:
        return {"status": "not_found", "customer_id": customer_id}
    return {"status": "found", "customer": customer}


if __name__ == "__main__":
    mcp.run(transport="stdio")
