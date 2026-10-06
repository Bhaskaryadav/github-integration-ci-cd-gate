#!/usr/bin/env bash
# PostToolUse hook — run bandit on Python files written by Claude Code.
set -euo pipefail

SEVERITY_LEVEL="${BANDIT_SEVERITY_LEVEL:-medium}"
FINDINGS_LOG="audit_log/bandit_findings.jsonl"
FILES_TO_SCAN="${CLAUDE_FILE_PATHS:-}"

if [[ -z "$FILES_TO_SCAN" ]]; then
  FILES_TO_SCAN=$(git diff --name-only --diff-filter=ACM 2>/dev/null | grep '\.py$' || true)
fi

PY_FILES=()
for f in $FILES_TO_SCAN; do
  if [[ "$f" == *.py ]] && [[ -f "$f" ]]; then
    PY_FILES+=("$f")
  fi
done

if [[ ${#PY_FILES[@]} -eq 0 ]]; then
  echo "[bandit-hook] No Python files to scan."
  exit 0
fi

mkdir -p audit_log
echo "[bandit-hook] Scanning: ${PY_FILES[*]}"

OUT=$(mktemp)
if bandit --format json --severity-level "$SEVERITY_LEVEL" --output "$OUT" "${PY_FILES[@]}" 2>/dev/null; then
  echo "[bandit-hook] Clean scan."
  rm -f "$OUT"
  exit 0
fi

COUNT=$(python3 -c "import json; print(len(json.load(open('$OUT')).get('results', [])))" 2>/dev/null || echo "1")
echo "[bandit-hook] FINDINGS: $COUNT issue(s) at ${SEVERITY_LEVEL}+ severity. Log: $FINDINGS_LOG"
rm -f "$OUT"
exit 1
