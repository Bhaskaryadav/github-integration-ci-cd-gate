# Project 3 — Concepts Deep Dive

## End-to-end PR automation flow

```
Claude Code session
    │
    ├─ GitHub MCP: list_issues → create_branch
    ├─ Edit chatbot.py (guardrails)
    ├─ PostToolUse hook → bandit scan on .py writes
    ├─ PreToolUse hook → audit_log/mcp_tool_calls.jsonl
    ├─ GitHub MCP: push_files → create_pull_request
    │
    ▼
GitHub Actions (on pull_request)
    ├─ Job 1: pci-dss-check (bandit + headless claude -p)
    ├─ Job 2: compliance-scoring (Claude-as-Judge 1–5)
    └─ Job 3: gate-summary (both must pass)
```

## Three chatbot guardrails

| Guardrail | Purpose | PCI DSS tie-in |
|-----------|---------|----------------|
| `pre_response_pii_filter` | Redact PAN/account patterns in responses | Req 3 — protect cardholder data |
| `rate_limit_check` | Max 20 financial queries/session | Req 6 — abuse prevention |
| `write_audit_log_entry` | JSONL audit per tool call | Req 10 — audit trail |

## Claude Code hooks

| Event | When | This lab |
|-------|------|----------|
| **PreToolUse** | Before any tool runs | Log tool name + sanitized input to JSONL |
| **PostToolUse** | After Write/Edit | Run bandit on changed `.py` files |

Hooks are configured in `.claude/settings.json` under `"hooks"`.

## Headless Claude Code in CI

```bash
claude -p "Analyze this diff for PCI DSS violations..." \
  --output-format stream-json \
  --no-interactive
```

CI parses `stream-json` events to extract the final JSON verdict.

## Claude-as-Judge gate

- Separate Claude instance scores PR quality 1–5
- **Threshold:** score ≥ 4 to pass
- Independent from PCI scan — both must pass
