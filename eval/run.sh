#!/usr/bin/env bash
# Runs every prompt in eval/prompts.txt under each arm, REPS times, with Claude Code in print mode.
#   base     no instructions
#   full     skills/ste/rules.md: every ASD-STE100 rule, restated for software (no linter)
#   skill    skills/ste/SKILL.md body
# No arm has tools, so the answer is prose only.
# CLAUDE_CONFIG_DIR holds only the login: no CLAUDE.md, hook or plugin leaks in.
# Usage: eval/run.sh OUT_DIR [REPS] [MODEL]
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
out=$(realpath -m "$1") reps=${2:-3} model=${3:-claude-opus-5-5}
mkdir -p "$out/cfg" "$out/cwd"
cp ~/.claude/.credentials.json "$out/cfg/"
awk 'n>=2; /^---$/{n++}' "$root/skills/ste/SKILL.md" > "$out/skill.md"
: > "$out/empty.md"

run() { # arm prompt-index rep prompt
  local arm=$1 i=$2 r=$3 p=$4 extra=()
  local f="$out/$arm.$i.$r.json"
  [[ -s $f ]] && return 0
  case $arm in
    base) extra=(--tools "" --append-system-prompt-file "$out/empty.md") ;;
    full) extra=(--tools "" --append-system-prompt-file "$root/skills/ste/rules.md") ;;
    skill) extra=(--tools "" --append-system-prompt-file "$out/skill.md") ;;
  esac
  (cd "$out/cwd" && CLAUDE_CONFIG_DIR="$out/cfg" claude -p --model "$model" --output-format json "${extra[@]}" "$p") > "$f.tmp"
  mv "$f.tmp" "$f"
  echo "done $arm.$i.$r"
}

export -f run; export out root model
i=0
while IFS= read -r p; do # interleaved arms, a pool of 9 calls
  i=$((i + 1))
  for r in $(seq "$reps"); do for arm in base full skill; do printf '%s\0%s\0%s\0%s\0' "$arm" "$i" "$r" "$p"; done; done
done < "$root/eval/prompts.txt" | xargs -0 -n4 -P9 bash -c 'run "$@"' _
echo "all runs done: $out"
