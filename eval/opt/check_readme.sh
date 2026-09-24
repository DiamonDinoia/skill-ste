#!/usr/bin/env bash
# D2 check: README is short, keeps its required sections, and its benchmark tables
# are rendered (eval/opt/tables.py) from the PASS transcript of the installed skill body.
set -uo pipefail
cd "$(dirname "$0")/../.."
fail=0
size=$(wc -c < README.md)
[ "$size" -le 6000 ] || { echo "FAIL: README.md is $size bytes, cap 6000"; fail=1; }
for anchor in 'claude plugin marketplace add DiamonDinoia/ste-skill' 'claude plugin install ste@ste' \
              'codex plugin marketplace add' 'gemini extensions install' \
              'npx skills add' 'gh skill install' 'git clone' \
              'Without the skill' 'With the skill' 'data race' \
              'test/run.sh' 'eval/' 'ste.py build' 'MIT' 'ASD'; do
  grep -qF "$anchor" README.md || { echo "FAIL: README.md lost anchor: $anchor"; fail=1; }
done
# Bind the tables to the installed skill: the transcript name carries the body hash.
H=$(awk 'n>=2; /^---$/{n++}' skills/ste/SKILL.md | sha256sum | cut -c1-12)
T="eval/opt/results/SKILL-$H.json"
if [ ! -f "$T" ]; then
  echo "FAIL: no PASS transcript for the installed skill body (want $T; run bash eval/opt/check.sh)"
  fail=1
else
  python3 eval/opt/tables.py "$T" --check README.md || fail=1
fi
[ "$fail" = 0 ] && echo "PASS: README.md $size bytes, anchors present, tables match $T"
exit "$fail"
