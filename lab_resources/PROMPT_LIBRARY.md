# Project 3 — Prompt Library

---

## GitHub MCP

### List compliance issues
```
Use GitHub MCP to list open issues in this repository.
Highlight any with labels compliance or security.
```

### Create branch
```
Using GitHub MCP, create branch feature/chatbot-compliance-guardrails from main.
Update my local git checkout to match.
```

### Push and PR
```
Use GitHub MCP push_files to commit banking_chatbot/chatbot.py on
feature/chatbot-compliance-guardrails with message:
"feat(chatbot): add PCI DSS compliance guardrails"

Then create_pull_request to main using the template in
starter_files/resources/pr_description_template.md
```

---

## Guardrail implementation

```
Extend banking_chatbot/chatbot.py with:
pre_response_pii_filter, rate_limit_check (20 financial queries/session),
write_audit_log_entry (audit_log/chatbot_tool_calls.jsonl),
run_with_guardrails() wrapper.
Reference starter_files/resources/guardrails_reference.py for patterns.
No plaintext PII in audit logs.
```

---

## Hook verification

```
Add a one-line comment to banking_chatbot/chatbot.py so PostToolUse bandit hook fires.
Show me the bandit output.
```

```
Make any MCP tool call, then show the last line of audit_log/mcp_tool_calls.jsonl
```

---

## CI debugging

```
Read .github/workflows/claude-security-gate.yml and explain:
1. Which env vars route Claude Code through OpenRouter?
2. What score fails the compliance gate?
3. What triggers workflow skip?
```
