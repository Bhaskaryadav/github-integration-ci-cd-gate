# Claude Code Hook Scripts — Module 6 Project 3

These scripts are **templates** for `.claude/settings.json` hooks. Project 3 walks you through copying and wiring them.

## Windows lab environments

Hook scripts are written in **bash** (`.sh`). On Windows, use one of:

| Option | How |
|--------|-----|
| **Git Bash** (recommended) | Install Git for Windows; run Claude Code from Git Bash |
| **WSL** | Run Claude Code inside Ubuntu WSL |
| **PowerShell** | Use the simplified `bandit_scan.ps1` for PostToolUse only |

In `.claude/settings.json`, point the `command` to the shell you use:

```json
"command": "bash scripts/hooks/bandit_scan.sh"
```

Or on PowerShell-only setups:

```json
"command": "powershell -ExecutionPolicy Bypass -File scripts/hooks/bandit_scan.ps1"
```

## Files

| File | Hook event | Purpose |
|------|------------|---------|
| `bandit_scan.sh` | PostToolUse | Run bandit after Python file writes |
| `mcp_audit_logger.sh` | PreToolUse | Log tool calls to `audit_log/mcp_tool_calls.jsonl` |
| `bandit_scan.ps1` | PostToolUse | Windows PowerShell alternative |

## Make scripts executable (Git Bash / Linux)

```bash
chmod +x scripts/hooks/*.sh
```
