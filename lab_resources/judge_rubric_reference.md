# Claude-as-Judge Rubric (CI Reference)

Used in `claude-security-gate.yml` compliance-scoring job.

## Scores

| Score | Grade | Gate |
|-------|-------|------|
| 5 | EXCELLENT | PASS |
| 4 | GOOD | PASS (minimum threshold) |
| 3 | ADEQUATE | FAIL |
| 2 | POOR | FAIL |
| 1 | CRITICAL_FAILURE | FAIL |

## Dimensions evaluated

1. Sensitive data masking/encryption
2. Audit logging for financial operations
3. Input validation on user-provided data
4. No hardcoded credentials
5. Error handling without information leakage
6. Alignment with CLAUDE.md PCI DSS standards

## JSON output shape

```json
{
  "score": 4,
  "grade": "GOOD",
  "gate_decision": "PASS",
  "strengths": ["..."],
  "improvements_required": ["..."],
  "pci_dss_notes": "...",
  "reviewer_summary": "..."
}
```

## Experiment

Intentionally leave a hardcoded API key in a test branch PR. Observe score drop and gate failure. Revert and re-push.
