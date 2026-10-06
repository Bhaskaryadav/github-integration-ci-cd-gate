"""
REFERENCE: chatbot guardrails for Project 3.
Merge into banking_chatbot/chatbot.py — adapt to your existing structure.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

FINANCIAL_KEYWORDS = frozenset({
    "balance", "transfer", "account", "statement", "loan",
    "credit", "debit", "transaction", "payment",
})

_session_counts: dict[str, int] = {}
AUDIT_PATH = Path("audit_log/chatbot_tool_calls.jsonl")


def is_financial_query(message: str) -> bool:
    return bool(set(message.lower().split()) & FINANCIAL_KEYWORDS)


def pre_response_pii_filter(response: str) -> str:
    response = re.sub(r"\b\d{13,19}\b", "[REDACTED-CARD]", response)
    response = re.sub(r"\b\d{8,12}\b", "[REDACTED-ACCT]", response)
    return response


def rate_limit_check(session_id: str, user_message: str) -> None:
    if not is_financial_query(user_message):
        return
    count = _session_counts.get(session_id, 0) + 1
    _session_counts[session_id] = count
    if count > 20:
        raise RuntimeError(f"Rate limit exceeded: {count} financial queries in session {session_id}")


def write_audit_log_entry(event: dict) -> None:
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": "CHATBOT_TOOL_CALL",
        **event,
    }
    with open(AUDIT_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def run_with_guardrails(user_message: str, session_id: str, handler) -> str:
    rate_limit_check(session_id, user_message)
    raw = handler(user_message)
    filtered = pre_response_pii_filter(raw)
    write_audit_log_entry({
        "session_id": session_id,
        "financial_query": is_financial_query(user_message),
        "response_length": len(filtered),
    })
    return filtered
