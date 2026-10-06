# Project 3 — Troubleshooting

## GitHub MCP 401/403

- Regenerate PAT with `repo` + `workflow` scopes
- Use `${GITHUB_PERSONAL_ACCESS_TOKEN}` in settings.json — never hardcode

## Hooks not firing

- Restart `claude` after editing `.claude/settings.json`
- `chmod +x scripts/hooks/*.sh`
- PostToolUse matcher must include `Write|Edit|MultiEdit`

## Bandit not installed

```bash
pip install bandit
bandit --version
```

## CI workflow never triggers

- Workflow must be on default branch or feature branch with open PR to `main`
- Check `paths:` filter includes your changed `.py` files
- `OPENROUTER_API_KEY` secret must exist in repo Settings → Actions

## compliance-scoring score 0 (grade: UNKNOWN)

- Root cause (fixed in the bundled `claude-security-gate.yml`): the workflow used to run `claude --output-format stream-json` and filter for a `content_block_delta` event to pull out Claude's answer. That's the raw Anthropic Messages API SSE event name, not one of Claude Code CLI's stream-json event types (`system`/`assistant`/`user`/`result`) — the filter never matched anything, so the extracted text was always empty and both scoring jobs fell back to their error defaults (`score: 0`, `grade: UNKNOWN`).
- Fix: use `claude --output-format json` and read Claude's final answer from the `.result` field, as documented at `docs.claude.com/en/docs/claude-code/headless`.
- If your repo already has an older copy of the workflow pushed, re-copy `starter_files/claude-security-gate.yml` to `.github/workflows/claude-security-gate.yml` and push, then re-run the workflow.
- If the score is still 0 after that: check the Actions log for auth errors, and verify `ANTHROPIC_API_KEY=""` plus `OPENROUTER_API_KEY` are set correctly in the workflow env block/secrets.

## validate_p3.py fails

Run from repo root:
```bash
python M6_P3_GitHub_CI_CD_Gate/starter_files/validate_p3.py
```

Default checks `M6_P3_GitHub_CI_CD_Gate/workspace/`.
