"""
Module 3 — Banking Chatbot (lab stub)
Extended in Module 6 Project 3 with PCI DSS compliance guardrails:

| Guardrail                | PCI DSS requirement                              |
|--------------------------|--------------------------------------------------|
| pre_response_pii_filter  | Req 3  — protect stored cardholder data          |
| rate_limit_check         | Req 6  — secure systems and applications         |
| write_audit_log_entry    | Req 10 — track access to network resources       |
| run_with_guardrails      | Chains all three on every response path          |
"""

from __future__ import annotations

import json
import re
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from llm_client import get_llm_client, resolve_model

load_dotenv()

FINANCIAL_KEYWORDS = frozenset({
    "balance", "transfer", "account", "statement", "loan",
    "credit", "debit", "transaction", "payment",
})

MAX_FINANCIAL_QUERIES_PER_SESSION = 20
MAX_MESSAGE_LENGTH = 4000
AUDIT_LOG_PATH = Path("audit_log/chatbot_tool_calls.jsonl")

# PAN: 13–19 digits, optionally grouped by spaces or dashes (e.g. 4111 1111 1111 1111)
_CARD_PATTERN = re.compile(r"\b(?:\d[ -]?){12,18}\d\b")
_ACCOUNT_PATTERN = re.compile(r"\b\d{8,12}\b")

# In-memory session counter for rate limiting (per-process)
_session_query_counts: dict[str, int] = {}
_session_lock = threading.Lock()


class RateLimitExceededError(RuntimeError):
    """Raised when a session exceeds the financial query limit."""


def is_financial_query(user_message: str) -> bool:
    """Return True if the message looks like a financial query."""
    tokens = set(re.findall(r"[a-z]+", user_message.lower()))
    return bool(tokens & FINANCIAL_KEYWORDS)


def pre_response_pii_filter(response: str) -> str:
    """Redact card numbers (PAN) and account numbers before returning a response (PCI DSS Req 3)."""
    response = _CARD_PATTERN.sub("[REDACTED-CARD]", response)
    response = _ACCOUNT_PATTERN.sub("[REDACTED-ACCT]", response)
    return response


def rate_limit_check(session_id: str) -> None:
    """Count a financial query for the session; raise after the limit is exceeded (PCI DSS Req 6)."""
    with _session_lock:
        count = _session_query_counts.get(session_id, 0) + 1
        _session_query_counts[session_id] = count
    if count > MAX_FINANCIAL_QUERIES_PER_SESSION:
        raise RateLimitExceededError(
            f"Rate limit exceeded: more than {MAX_FINANCIAL_QUERIES_PER_SESSION} "
            "financial queries in this session"
        )


def _sanitize(value: Any) -> Any:
    """Recursively apply the PII filter so no plaintext card/account data reaches the logs."""
    if isinstance(value, str):
        return pre_response_pii_filter(value)
    if isinstance(value, dict):
        return {k: _sanitize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_sanitize(v) for v in value]
    return value


def write_audit_log_entry(event: dict) -> None:
    """Append a sanitized JSONL audit entry to audit_log/chatbot_tool_calls.jsonl (PCI DSS Req 10)."""
    AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": "CHATBOT_TOOL_CALL",
        **_sanitize(event),
    }
    with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def call_claude(user_message: str, tools: list[dict[str, Any]] | None = None) -> tuple[str, list[str]]:
    """Send a user message to Claude; return the text response and names of any tools requested."""
    client = get_llm_client()
    response = client.messages.create(
        model=resolve_model("claude-sonnet-4-5"),
        max_tokens=1024,
        tools=tools or [],
        messages=[{"role": "user", "content": user_message}],
    )
    text = ""
    tool_names: list[str] = []
    for block in response.content:
        if block.type == "text" and not text:
            text = block.text
        elif block.type == "tool_use":
            tool_names.append(block.name)
    return text, tool_names


def run_with_guardrails(user_message: str, session_id: str) -> str:
    """Chain rate limit → LLM/tool calls → audit log → PII filter before returning a response."""
    if not user_message or len(user_message) > MAX_MESSAGE_LENGTH:
        raise ValueError("Message must be between 1 and %d characters" % MAX_MESSAGE_LENGTH)

    financial = is_financial_query(user_message)
    if financial:
        try:
            rate_limit_check(session_id)
        except RateLimitExceededError:
            write_audit_log_entry({
                "session_id": session_id,
                "action": "RATE_LIMIT_BLOCKED",
                "financial_query": True,
            })
            raise

    # raw_response, tool_names = call_claude(user_message)
    
    # Required (capture arguments):
    tool_args = getattr(block, 'input', {})
    log_entry = {'tool_name': block.name, 'tool_args': tool_args}

    # Log metadata only — never the message or response text
    for tool_name in tool_names:
        write_audit_log_entry({
            "session_id": session_id,
            "action": "TOOL_CALL",
            "tool_name": tool_name,
        })
    write_audit_log_entry({
        "session_id": session_id,
        "action": "RESPONSE",
        "financial_query": financial,
        "tool_call_count": len(tool_names),
        "message_length": len(user_message),
    })

    return pre_response_pii_filter(raw_response)


def handle_message(user_message: str, session_id: str = "default") -> str:
    """Chatbot entry point — all responses pass through the PCI DSS guardrails."""
    try:
        return run_with_guardrails(user_message, session_id)
    except RateLimitExceededError:
        return "You have reached the limit for financial queries in this session. Please try again later."
    except ValueError:
        return "Your message could not be processed. Please shorten it and try again."
    except Exception:
        # Safe error message — no stack traces or internals to clients (CLAUDE.md PCI DSS #5)
        return "Sorry, something went wrong. Please try again later."


if __name__ == "__main__":
    print(handle_message("What services does Heritage National Bank offer?"))
