"""
Module 4 — Banking API MCP Server (HTTP/SSE)
Lab stub for Module 6 Project 1 validation. Listens on port 8080.

Live traffic monitor:
    Open http://localhost:8080/dashboard in a browser to watch
    every MCP tool call (request in, response out) in real time.
    Other lab MCP servers (customer-info, stdio) forward their
    events here via POST /ingest, so the dashboard shows
    platform-wide MCP traffic.
"""

from __future__ import annotations

import functools
import json
import re
import time
from collections import deque
from datetime import datetime, timezone
from typing import Any, Callable

try:
    from mcp.server.fastmcp import FastMCP
    from starlette.requests import Request
    from starlette.responses import HTMLResponse, JSONResponse
except ImportError as exc:
    raise SystemExit(
        "Missing dependency: pip install mcp uvicorn\n"
        f"Original error: {exc}"
    ) from exc

mcp = FastMCP(
    "banking-api",
    host="0.0.0.0",
    port=8080,
)

_ACCOUNTS: dict[str, dict[str, Any]] = {
    "ACC-2024-TEST-001": {
        "account_id": "ACC-2024-TEST-001",
        "balance_inr": 125000,
        "currency": "INR",
        "status": "active",
        "account_type": "Premium Savings",
    }
}

# ---------------------------------------------------------------------------
# Traffic monitor — records every tool call for the /dashboard view
# ---------------------------------------------------------------------------

_EVENTS: deque[dict[str, Any]] = deque(maxlen=200)
_STARTED_AT = time.time()
_PAN_PATTERN = re.compile(r"\b\d{13,19}\b")

# ANSI colours for terminal traffic log
_C_IN = "\033[96m"     # cyan
_C_OUT = "\033[92m"    # green
_C_DIM = "\033[2m"
_C_END = "\033[0m"


def _mask_pci(value: Any) -> Any:
    """Mask anything resembling a card PAN (PCI DSS Req 3) before display."""
    text = json.dumps(value, default=str)
    masked = _PAN_PATTERN.sub(lambda m: f"****{m.group(0)[-4:]}", text)
    return json.loads(masked)


def monitored(fn: Callable[..., Any]) -> Callable[..., Any]:
    """Record request/response of an MCP tool for the live dashboard."""

    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        started = time.perf_counter()
        result = fn(*args, **kwargs)
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        event = {
            "ts": datetime.now(timezone.utc).strftime("%H:%M:%S"),
            "server": "banking-api",
            "tool": fn.__name__,
            "request": _mask_pci(kwargs or {}),
            "response": _mask_pci(result),
            "ms": elapsed_ms,
        }
        _EVENTS.appendleft(event)
        print(
            f"{_C_IN}→ IN  {event['ts']}  {fn.__name__}"
            f"({json.dumps(event['request'])}){_C_END}"
        )
        print(
            f"{_C_OUT}← OUT {event['ts']}  {fn.__name__}  "
            f"{json.dumps(event['response'])[:120]}"
            f"  {_C_DIM}{elapsed_ms} ms{_C_END}"
        )
        return result

    return wrapper


# ---------------------------------------------------------------------------
# MCP tools
# ---------------------------------------------------------------------------


@mcp.tool()
@monitored
def get_account_balance(account_id: str) -> dict[str, Any]:
    """Return account balance for a lab account ID."""
    account = _ACCOUNTS.get(
        account_id,
        {
            "account_id": account_id,
            "balance_inr": 0,
            "currency": "INR",
            "status": "unknown",
        },
    )
    return account


@mcp.tool()
@monitored
def initiate_transfer(
    from_account: str,
    to_account: str,
    amount_inr: int,
) -> dict[str, Any]:
    """Initiate a mock transfer between accounts."""
    return {
        "status": "accepted",
        "from_account": from_account,
        "to_account": to_account,
        "amount_inr": amount_inr,
        "reference_id": "TXN-LAB-0001",
    }


@mcp.tool()
@monitored
def get_compliance_pipeline() -> list[dict[str, Any]]:
    """Return the compliance pipeline sequence (AML step before approval)."""
    return [
        {"step": 1, "name": "kyc_check", "description": "Verify customer identity"},
        {"step": 2, "name": "aml_analysis", "description": "Anti-money laundering screening"},
        {"step": 3, "name": "approval", "description": "Final compliance approval"},
    ]


@mcp.tool()
@monitored
def apply_for_loan(
    customer_id: str,
    loan_amount_inr: int,
    tenure_months: int,
) -> dict[str, Any]:
    """Submit a mock loan application."""
    return {
        "status": "submitted",
        "customer_id": customer_id,
        "loan_amount_inr": loan_amount_inr,
        "tenure_months": tenure_months,
        "application_id": "LOAN-LAB-0001",
    }


# ---------------------------------------------------------------------------
# Dashboard routes (same port 8080 — no extra process)
# ---------------------------------------------------------------------------


@mcp.custom_route("/events", methods=["GET"])
async def events(_: Request) -> JSONResponse:
    """JSON feed of recent tool-call events, newest first."""
    return JSONResponse(
        {
            "uptime_s": int(time.time() - _STARTED_AT),
            "total": len(_EVENTS),
            "events": list(_EVENTS),
        }
    )


@mcp.custom_route("/ingest", methods=["POST"])
async def ingest(request: Request) -> JSONResponse:
    """Accept tool-call events forwarded by other lab MCP servers (stdio)."""
    try:
        event = await request.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "invalid JSON"}, status_code=400)
    if not isinstance(event, dict) or "tool" not in event:
        return JSONResponse({"ok": False, "error": "missing 'tool'"}, status_code=400)
    event.setdefault("ts", datetime.now(timezone.utc).strftime("%H:%M:%S"))
    event.setdefault("server", "unknown")
    event["request"] = _mask_pci(event.get("request", {}))
    event["response"] = _mask_pci(event.get("response", {}))
    _EVENTS.appendleft(event)
    print(
        f"{_C_IN}→ IN  {event['ts']}  [{event['server']}] {event['tool']}"
        f"({json.dumps(event['request'])}){_C_END}"
    )
    print(
        f"{_C_OUT}← OUT {event['ts']}  [{event['server']}] {event['tool']}  "
        f"{json.dumps(event['response'])[:120]}{_C_END}"
    )
    return JSONResponse({"ok": True})


_DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Heritage National Bank — MCP Traffic Monitor</title>
<style>
  :root {
    --bg: #0d1117; --panel: #161b22; --border: #30363d;
    --text: #e6edf3; --dim: #8b949e;
    --in: #58a6ff; --out: #3fb950; --accent: #d29922; --alt: #bc8cff;
  }
  * { box-sizing: border-box; margin: 0; }
  body {
    background: var(--bg); color: var(--text);
    font: 14px/1.5 "SF Mono", "Cascadia Code", Consolas, monospace;
    padding: 24px; max-width: 1100px; margin: 0 auto;
  }
  header { display: flex; align-items: baseline; gap: 16px; flex-wrap: wrap;
           border-bottom: 1px solid var(--border); padding-bottom: 16px; }
  h1 { font-size: 18px; font-weight: 600; }
  h1 span { color: var(--accent); }
  .live { color: var(--out); font-size: 12px; }
  .live::before { content: "●"; animation: blink 1.4s infinite; margin-right: 5px; }
  @keyframes blink { 50% { opacity: .25; } }
  .stats { display: flex; gap: 12px; margin: 16px 0 20px; flex-wrap: wrap; }
  .stat { background: var(--panel); border: 1px solid var(--border);
          border-radius: 8px; padding: 10px 18px; min-width: 130px; }
  .stat b { display: block; font-size: 22px; font-weight: 600; }
  .stat span { color: var(--dim); font-size: 11px; text-transform: uppercase;
               letter-spacing: .08em; }
  .empty { color: var(--dim); text-align: center; padding: 60px 0;
           border: 1px dashed var(--border); border-radius: 8px; }
  .event { background: var(--panel); border: 1px solid var(--border);
           border-radius: 8px; margin-bottom: 12px; overflow: hidden;
           animation: slidein .3s ease; }
  @keyframes slidein { from { opacity: 0; transform: translateY(-6px); } }
  .event-head { display: flex; gap: 14px; align-items: center;
                padding: 8px 14px; border-bottom: 1px solid var(--border); }
  .badge { font-size: 11px; padding: 1px 8px; border-radius: 10px;
           border: 1px solid var(--accent); color: var(--accent); }
  .badge.alt { border-color: var(--alt); color: var(--alt); }
  .tool { color: var(--text); font-weight: 600; }
  .ts, .ms { color: var(--dim); font-size: 12px; }
  .ms { margin-left: auto; }
  .row { display: flex; gap: 10px; padding: 8px 14px; }
  .row + .row { border-top: 1px dashed var(--border); }
  .dir { flex: 0 0 52px; font-weight: 700; }
  .dir.in { color: var(--in); } .dir.out { color: var(--out); }
  pre { white-space: pre-wrap; word-break: break-all; color: var(--text);
        font-size: 13px; flex: 1; }
  footer { color: var(--dim); font-size: 12px; margin-top: 24px;
           border-top: 1px solid var(--border); padding-top: 12px; }
</style>
</head>
<body>
<header>
  <h1><span>Heritage National Bank</span> · MCP Traffic Monitor</h1>
  <div class="live">LIVE — polling every 2 s</div>
</header>

<div class="stats">
  <div class="stat"><b id="total">0</b><span>tool calls</span></div>
  <div class="stat"><b id="uptime">0s</b><span>server uptime</span></div>
  <div class="stat"><b>2</b><span>servers monitored</span></div>
  <div class="stat"><b>:8080/sse</b><span>MCP endpoint</span></div>
</div>

<div id="feed"><div class="empty">Waiting for MCP tool calls…<br><br>
Ask Claude Code: <i>"Use the banking-api MCP tool get_account_balance
for account ACC-2024-TEST-001"</i></div></div>

<footer>Monitors <b>banking-api</b> (this process, SSE) and <b>customer-info</b>
(stdio — events forwarded over localhost). PCI DSS note: values matching a
13–19 digit card pattern are masked to last 4 digits before display
(Requirement 3).</footer>

<script>
function fmt(s){const h=Math.floor(s/3600),m=Math.floor(s%3600/60);
  return h?`${h}h ${m}m`:m?`${m}m ${s%60}s`:`${s}s`;}
async function poll(){
  try{
    const r = await fetch("/events"); const d = await r.json();
    document.getElementById("total").textContent = d.total;
    document.getElementById("uptime").textContent = fmt(d.uptime_s);
    if(!d.events.length) return;
    document.getElementById("feed").innerHTML = d.events.map(e=>`
      <div class="event">
        <div class="event-head">
          <span class="badge ${e.server==="banking-api"?"":"alt"}">${e.server}</span>
          <span class="tool">${e.tool}</span>
          <span class="ts">${e.ts} UTC</span>
          <span class="ms">${e.ms ?? "—"} ms</span>
        </div>
        <div class="row"><span class="dir in">→ IN</span>
          <pre>${JSON.stringify(e.request, null, 1)}</pre></div>
        <div class="row"><span class="dir out">← OUT</span>
          <pre>${JSON.stringify(e.response, null, 1)}</pre></div>
      </div>`).join("");
  }catch(err){/* server restarting — keep polling */}
}
poll(); setInterval(poll, 2000);
</script>
</body>
</html>"""


@mcp.custom_route("/dashboard", methods=["GET"])
async def dashboard(_: Request) -> HTMLResponse:
    """Live traffic monitor UI."""
    return HTMLResponse(_DASHBOARD_HTML)


if __name__ == "__main__":
    print("INFO: Banking API MCP Server starting...")
    print("INFO: Listening on http://0.0.0.0:8080")
    print("INFO: SSE endpoint:       http://localhost:8080/sse")
    print("INFO: Traffic dashboard:  http://localhost:8080/dashboard  <-- open in browser")
    print("INFO: Event ingest:       POST /ingest (customer-info forwards events here)")
    print("INFO: Registered tools: get_account_balance, initiate_transfer, "
          "get_compliance_pipeline, apply_for_loan")
    print("INFO: API Key authentication: ENABLED (set BANKING_MCP_API_KEY)")
    mcp.run(transport="sse")
