# CLAUDE.md — Heritage National Bank AI Platform

> Authoritative context for Claude Code sessions. Keep accurate and concise.

## Platform Architecture

```
Skills.md Library  →  MCP Tool Layer (3 servers)  →  Claude API  →  Banking Application Layer
```

## MCP Server Registry

| Server | Transport | Tools |
|--------|-----------|-------|
| customer-info | stdio | store/retrieve customer |
| banking-api | SSE :8080 | get_account_balance, initiate_transfer, apply_for_loan |
| github | stdio | list_issues, create_branch, push_files, create_pull_request |

## PCI DSS Standards — MANDATORY

1. No plaintext card data in logs — mask to last 4 digits
2. No hardcoded credentials — use environment variables
3. Input sanitization on all banking API calls
4. Audit logging for tool calls → `audit_log/`
5. Safe error messages — no stack traces to clients

## Model Routing

| Task | Model |
|------|-------|
| Simple lookups | claude-haiku-4-5 |
| Compliance summaries | claude-sonnet-4-5 |
| Complex reasoning | claude-opus-4-5 |
