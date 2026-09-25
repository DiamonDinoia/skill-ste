#!/usr/bin/env bash
# Builds the test image, then runs test/install.sh in fresh containers:
#   1. on this repository: every harness must install and see the skill;
#   2. on a copy whose SKILL.md name is invalid: the run must fail (positive control).
# Usage: test/run.sh [docker|podman]
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
engine=${1:-$(command -v podman >/dev/null && echo podman || echo docker)}
"$engine" --version
"$engine" build -t skill-ste-test "$root/test"

run() { "$engine" run --rm -v "$1:/repo:ro" -v "$root/test/install.sh:/install.sh:ro" skill-ste-test bash /install.sh /repo; }

# The linter is stdlib only: every Python it claims runs it, dictionary or not.
echo "== ste.py on Python 3.9 to 3.14"
if uv --version >/dev/null 2>&1; then
  for v in 3.9 3.10 3.11 3.12 3.13 3.14; do
    got=$(echo 'We set up the tile.' | STE_HOME=$(mktemp -d) uv run -q --no-project --python "$v" \
      "$root/skills/ste/scripts/ste.py" lint) && s=0 || s=$?
    want=$'-:1: person: We\n-:1: phrasal: set up'
    [[ $s == 1 && $got == "$want"* ]] || { echo "FAIL python $v: exit $s: $got"; exit 1; }
    echo "PASS python $v"
  done
else
  echo "SKIP python 3.9 to 3.14: uv is not installed"
fi
echo "== repository"
run "$root"

echo "== positive control: SKILL.md name 'STE_bad' must fail"
bad=$(mktemp -d)
trap 'rm -rf "$bad"' EXIT
cp -r "$root/." "$bad/"
chmod -R a+rX "$bad"  # mktemp -d is 0700: the container user must read the copy
sed -i 's/^name: ste$/name: STE_bad/' "$bad/skills/ste/SKILL.md"
if log=$(run "$bad" 2>&1); then echo "$log"; echo "control FAILED: the broken skill passed"; exit 1; fi
echo "$log"
# The failure must come from the name check, not from an unreadable mount.
if ! grep -q '^FAIL frontmatter name/description' <<<"$log" || grep -qiE 'EACCES|permission denied' <<<"$log"; then
  echo "control FAILED: the run failed, but not on the invalid name"; exit 1
fi
echo "control PASSED: the broken skill failed on the name check"
