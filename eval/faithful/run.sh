#!/usr/bin/env bash
# Round trip on the STE examples of ASD-STE100 Part 1 (refs.jsonl):
#   1. a model with no instructions rewrites each reference in ordinary English (plain.N.json);
#   2. each arm rewrites that plain text back into STE (ARM.N.json).
# score.py compares each rewrite with the reference. ARM=FILE: FILE goes into the system prompt.
# An arm name that ends in "-lint" may also run `ste.py lint`.
# Usage: eval/faithful/run.sh OUT_DIR ARM=FILE...
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
root=$(cd "$here/../.." && pwd)
out=$(realpath -m "$1"); shift
model=${MODEL:-claude-opus-5-5}
mkdir -p "$out/cfg" "$out/cwd"
cp ~/.claude/.credentials.json "$out/cfg/"
: > "$out/empty.md"

ask() { # out-file system-file tools prompt
  [[ -s $1 ]] && return 0
  local tools=(--tools "")
  [[ $3 == lint ]] && tools=(--tools Bash --allowedTools "Bash(python3 $root/skills/ste/scripts/ste.py lint*)")
  (cd "$out/cwd" && CLAUDE_CONFIG_DIR="$out/cfg" claude -p --model "$model" --output-format json "${tools[@]}" \
    --append-system-prompt-file "$2" "$4") > "$1.tmp"
  mv "$1.tmp" "$1"
  echo "done $(basename "$1")"
}
export -f ask; export out root model

to_plain='Rewrite this technical text the way a typical engineer writes an informal note or email: natural wording, '\
'contractions, phrasal verbs, passive voice where it is natural, longer sentences. Keep every fact, number and '\
'identifier. Output only the rewritten text.'
to_ste='Rewrite this text in Simplified Technical English. Keep every fact, number and identifier. '\
'Output only the rewritten text.'

[[ -f $here/refs.jsonl ]] || python3 "$here/extract.py"  # the texts are (c) ASD: built locally
n=$(wc -l < "$here/refs.jsonl")
for i in $(seq "$n"); do
  ref=$(sed -n "${i}p" "$here/refs.jsonl" | python3 -c 'import json,sys; print(json.load(sys.stdin)["ste"])')
  printf '%s\0' "$out/plain.$i.json" "$out/empty.md" none "$to_plain"$'\n\n'"$ref"
done | xargs -0 -n4 -P9 bash -c 'ask "$@"' _

for i in $(seq "$n"); do
  plain=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["result"])' "$out/plain.$i.json")
  for spec in "$@"; do
    arm=${spec%%=*} file=$(realpath "${spec#*=}")
    tools=none; [[ $arm == *-lint ]] && tools=lint
    printf '%s\0' "$out/$arm.$i.json" "$file" "$tools" "$to_ste"$'\n\n'"$plain"
  done
done | xargs -0 -n4 -P9 bash -c 'ask "$@"' _
echo "all runs done: $out"
