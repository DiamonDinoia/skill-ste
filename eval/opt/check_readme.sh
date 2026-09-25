#!/usr/bin/env bash
# D2 check: README is short, keeps its required sections, and its Results gate table
# matches the committed tournament transcript (eval/opt/results/tournament.md) verbatim.
set -uo pipefail
cd "$(dirname "$0")/../.."
fail=0
size=$(wc -c < README.md)
[ "$size" -le 6000 ] || { echo "FAIL: README.md is $size bytes, cap 6000"; fail=1; }
for anchor in 'claude plugin marketplace add DiamonDinoia/skill-ste' 'claude plugin install ste@ste' \
              'codex plugin marketplace add' 'codex plugin add ste@ste' 'gemini extensions install' \
              'npx skills add' 'gh skill install' 'git clone' \
              'Without the skill' 'With the skill' 'data race' 'Kimi-K3' \
              'test/run.sh' 'eval/' 'ste.py build' 'MIT' 'ASD' 'chrF'; do
  grep -qF "$anchor" README.md || { echo "FAIL: README.md lost anchor: $anchor"; fail=1; }
done
# Provenance: every candidate row of the tournament gate table appears in the README
# (whitespace-insensitive), so the Results numbers come from the committed transcript.
python3 - <<'EOF'
import re, sys
t = open("eval/opt/results/tournament.md").read()
rows = [l for l in t.splitlines() if re.match(r"\|\s*[A-H]\s*\|", l)]
def norm(s):
    return re.sub(r"\s+", "", s).replace("|", "")
readme = norm(open("README.md").read())
missing = [r.strip() for r in rows if norm(r) not in readme]
if missing:
    print("FAIL: README lacks these tournament gate rows:")
    print("\n".join(missing))
    sys.exit(1)
print(f"PASS: README carries all {len(rows)} tournament gate rows")
EOF
[ $? = 0 ] || fail=1
[ "$fail" = 0 ] && echo "PASS: README.md $size bytes, anchors present, gate table matches tournament.md"
exit "$fail"
