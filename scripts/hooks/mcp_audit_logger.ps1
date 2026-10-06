# PreToolUse hook — append tool call metadata to audit_log/mcp_tool_calls.jsonl (Windows)
$AuditDir = if ($env:AUDIT_LOG_DIR) { $env:AUDIT_LOG_DIR } else { "audit_log" }
New-Item -ItemType Directory -Force -Path $AuditDir | Out-Null
$raw = [Console]::In.ReadToEnd()
if (-not $raw) { $raw = "{}" }
$env:HOOK_INPUT_PASSTHROUGH = $raw
$env:AUDIT_LOG_DIR = $AuditDir

python -c @"
import json, datetime, os, re
raw = os.environ.get('HOOK_INPUT_PASSTHROUGH', '{}')
try:
    data = json.loads(raw) if raw.strip() else {}
except json.JSONDecodeError:
    data = {}
tool_name = data.get('tool_name', 'unknown')
tool_input = data.get('tool_input', {})
session_id = data.get('session_id', os.environ.get('CLAUDE_SESSION_ID', 'unknown'))
PII = [re.compile(r'\b[0-9]{10,16}\b')]
def sanitize(val):
    if isinstance(val, str):
        for p in PII:
            val = p.sub('[REDACTED-PCI]', val)
        return val
    if isinstance(val, dict):
        return {k: sanitize(v) for k, v in val.items()}
    if isinstance(val, list):
        return [sanitize(i) for i in val]
    return val
entry = {
    'timestamp': datetime.datetime.utcnow().isoformat() + 'Z',
    'hook_event': 'PreToolUse',
    'session_id': session_id,
    'tool_name': tool_name,
    'tool_input': sanitize(tool_input),
    'is_mcp_tool': '.' in str(tool_name),
    'schema_version': '1.0',
}
path = os.path.join(os.environ.get('AUDIT_LOG_DIR', 'audit_log'), 'mcp_tool_calls.jsonl')
with open(path, 'a', encoding='utf-8') as f:
    f.write(json.dumps(entry) + '\n')
prefix = '[mcp-audit]' if '.' in str(tool_name) else '[tool-audit]'
print(f'{prefix} Logged: {tool_name}')
"@

exit 0
