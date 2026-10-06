# Pull Request: Chatbot Compliance Guardrails

## Summary

Adds three PCI DSS-aligned guardrails to `banking_chatbot/chatbot.py` on branch `feature/chatbot-compliance-guardrails`.

## Guardrails

| Guardrail | Function | PCI DSS | Behaviour |
|-----------|----------|---------|-----------|
| PII filter | `pre_response_pii_filter()` | Req 3 | Redacts card/account patterns before response |
| Rate limit | `rate_limit_check()` | Req 6 | Raises after 20 financial queries per session |
| Audit log | `write_audit_log_entry()` | Req 10 | Appends JSONL to `audit_log/chatbot_tool_calls.jsonl` |

## Wrapper

`run_with_guardrails(user_message, session_id)` chains all three before returning.

## References

- CLAUDE.md — PCI DSS Standards section
- Module 3 banking chatbot baseline (`banking_chatbot/chatbot.py`)

## Test notes

- Input containing `4111111111111111` → redacted in output
- 21st financial query in same session → rate limit error

## CI expectation

- `pci-dss-check` — no critical/high findings
- `compliance-scoring` — score ≥ 4/5
