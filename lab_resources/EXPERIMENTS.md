# Project 3 — Experiment Lab

---

## Experiment 1: Hook failure injection

1. Temporarily add `api_key = "sk-live-bad"` to a test `.py` file via Claude Code
2. Observe bandit hook output (PostToolUse)
3. Remove the line

**Observe:** Hook surfaces findings before you continue editing.

---

## Experiment 2: Audit log PII sanitization

1. Trigger MCP call with a fake account number in tool input
2. Read `audit_log/mcp_tool_calls.jsonl`
3. Confirm `[REDACTED-PCI]` or no raw 16-digit numbers

---

## Experiment 3: Gate failure on purpose

1. Create branch `experiment/ci-fail-test`
2. Add hardcoded password to a Python file
3. Open PR — watch `pci-dss-check` fail
4. Close PR without merging

---

## Experiment 4: Headless PCI prompt locally

```bash
git diff main...HEAD -- '*.py' > /tmp/pr_diff.patch
claude -p "Review this diff for PCI DSS violations. Output JSON with violations list and overall_pci_status PASS or FAIL. DIFF: $(head -100 /tmp/pr_diff.patch)"
```

Compare output to GitHub Actions artifact.

---

## Experiment 5: PR comment bot

After compliance-scoring job runs, find the automated PR comment with score bar (🟦🟦🟦🟦⬜). Note grade and gate decision.

---

## Experiment 6: Rate limit simulation

```python
from banking_chatbot.chatbot import run_with_guardrails, handle_message
for i in range(22):
    try:
        run_with_guardrails("what is my balance", "sess-1", handle_message)
    except RuntimeError as e:
        print(f"Stopped at query {i+1}: {e}")
        break
```

---

## Extension challenge (+15 min)

**Fail-then-fix CI loop:** Open a deliberate PCI violation PR, capture failed gate screenshot, fix, push again, capture pass screenshot. Add both to submission evidence.
