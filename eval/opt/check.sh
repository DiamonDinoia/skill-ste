#!/usr/bin/env bash
# D1 check: the skill body in $1 beats the frozen baseline body on the 4 gateway models.
# Usage: bash eval/opt/check.sh skills/ste/SKILL.md
set -euo pipefail
cd "$(dirname "$0")/../.."
export LLM_BASE_URL="${LLM_BASE_URL:-https://inference.flatironinstitute.org/v1}"
export LLM_API_KEY="${LLM_API_KEY:-$KIMI_K3_GW_API_KEY}"
# The frozen baseline: the skill body at the interview commit, never the live file.
# No truncating redirect: the body lands in a temp file first, cur.md is replaced whole.
grep -qE '^name:[[:space:]]*ste[[:space:]]*$' "$1" && grep -q '^description: ' "$1" \
  || { echo "FAIL: frontmatter must carry 'name: ste' and a description"; exit 1; }
TMP_BODY=$(mktemp /tmp/ste-cand-XXXXXX.md)
awk 'n>=2; /^---$/{n++}' "$1" > "$TMP_BODY"
git show 1d17df2:skills/ste/SKILL.md | awk 'n>=2; /^---$/{n++}' > eval/opt/cur.md.tmp
mv eval/opt/cur.md.tmp eval/opt/cur.md
NAME="SKILL-$(sha256sum "$TMP_BODY" | cut -c1-12)"
python3 eval/opt/compare.py "$TMP_BODY" --name "$NAME"
