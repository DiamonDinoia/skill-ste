#!/usr/bin/env bash
# Positive controls for the acceptance gate, at gate config (Kimi-K3, cached after the tournament).
# Each control must make compare.py exit 1; a gate that cannot fail is not a gate.
set -uo pipefail
cd "$(dirname "$0")/../.."
export LLM_BASE_URL="${LLM_BASE_URL:-https://inference.flatironinstitute.org/v1}"
export LLM_API_KEY="${LLM_API_KEY:-$KIMI_K3_GW_API_KEY}"
fail=0
for c in control_same control_empty; do
  if python3 eval/opt/compare.py "eval/opt/$c.md" --gate --name "ctrl_$c" >/dev/null 2>&1; then
    echo "FAIL: gate passed $c (a gate that passes $c cannot fail)"; fail=1
  else
    echo "PASS: gate rejected $c"
  fi
done
# tables.py unit control: a README missing the tables must fail --check
python3 -c "
import subprocess, sys
r = subprocess.run(['python3', 'eval/opt/tables.py', 'eval/opt/results/ctrl_control_same-fail.json',
                    '--check', 'README.md'], capture_output=True)
print('PASS: tables.py --check rejects the current README' if r.returncode
      else 'FAIL: tables.py --check passed a README without the rendered tables')
sys.exit(0 if r.returncode else 1)
" || fail=1
exit "$fail"
