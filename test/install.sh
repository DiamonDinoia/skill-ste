#!/usr/bin/env bash
# Installs the skill from /repo with the mechanism of each harness, then proves each one sees it.
# Runs inside test/Dockerfile. Collects every result and fails at the end.
set -uo pipefail
repo=${1:-/repo}
fail=0
has() { [[ -f $1 ]] && grep -q "$2" "$1"; } # file, pattern
export -f has
check() { # name, command...
  local name=$1; shift
  if out=$("$@" 2>&1); then echo "PASS $name"; else echo "FAIL $name"; echo "$out" | tail -20; fail=1; fi
}

# Every CLI answers its own --version before anything is gated on it.
for c in claude codex gemini opencode skills gh; do check "$c --version: $($c --version 2>&1 | head -1)" "$c" --version; done

# Skill format: agentskills.io name rule and the 1024-character description limit.
check "frontmatter name/description" python3 - "$repo/skills/ste/SKILL.md" <<'EOF'
import re, sys
text = open(sys.argv[1]).read()
fm = text.split("---")[1]
name = re.search(r"^name: (.+)$", fm, re.M).group(1).strip()
desc = re.search(r"^description: (.+)$", fm, re.M).group(1).strip()
assert re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name) and len(name) <= 64 and name == "ste", name
assert 1 <= len(desc) <= 1024, len(desc)
print(f"name={name} description={len(desc)} chars")
EOF

# Claude Code: plugin marketplace.
check "claude plugin validate --strict" claude plugin validate "$repo" --strict
check "claude marketplace add" claude plugin marketplace add "$repo"
check "claude plugin install" claude plugin install ste@ste --scope user
check "claude skill on disk" bash -c 'f=$(find ~/.claude/plugins -path "*skills/ste/SKILL.md" | head -1); has "$f" "^name: ste" && echo "$f"'
check "claude plugin list shows ste" bash -c 'claude plugin list | grep -q "ste@ste"'
# The SessionStart hook of the installed copy prints the skill body without the frontmatter.
check "claude SessionStart hook prints the skill body" bash -c \
  'root=$(dirname "$(find ~/.claude/plugins -path "*/hooks/hooks.json" | head -1)")/..
   cmd=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))[\"hooks\"][\"SessionStart\"][0][\"hooks\"][0][\"command\"])" "$root/hooks/hooks.json")
   out=$(CLAUDE_PLUGIN_ROOT=$root bash -c "$cmd") && dir=${out##*The skill directory is } && echo "$out"
   [[ $out == *"Write all prose"* && $out != *"name: ste"* && -f ${dir%.}/scripts/ste.py ]]'

# Codex: plugin marketplace (reads .claude-plugin/marketplace.json) and the skills directory.
check "codex marketplace add" codex plugin marketplace add "$repo"
check "codex marketplace list shows ste" bash -c 'codex plugin marketplace list | grep -q ste'

# Gemini CLI: extension.
check "gemini extension install" bash -c "yes | gemini extensions install '$repo' --consent"
check "gemini extensions list shows ste" bash -c 'gemini extensions list 2>&1 | grep -q ste'
check "gemini skill on disk" has ~/.gemini/extensions/ste/skills/ste/SKILL.md "^name: ste"

# skills CLI: one command for Codex, opencode, Cursor and Copilot directories.
check "npx skills add" skills add "$repo" --skill ste -g -y -a codex -a opencode -a cursor -a github-copilot
# skills 1.7 writes one copy to ~/.agents/skills: Codex, opencode, Cursor, Copilot read it.
check "skills CLI -> ~/.agents/skills" has ~/.agents/skills/ste/SKILL.md "^name: ste"
check "skills ls -g shows ste" bash -c 'skills ls -g 2>&1 | grep -q ste'

# gh skill: --from-local installs the checkout. The README form installs OWNER/REPO.
check "gh skill install" gh skill install "$repo" ste --from-local --agent claude-code --scope user
check "gh skill on disk" has ~/.claude/skills/ste/SKILL.md "^name: ste"

# By hand, as in the README, in a fresh home: gh skill already wrote ~/.claude/skills/ste.
manual=$(mktemp -d)
check "manual symlink" bash -c "mkdir -p '$manual/.claude/skills' && ln -s '$repo/skills/ste' '$manual/.claude/skills/ste'"
check "manual skill on disk" has "$manual/.claude/skills/ste/SKILL.md" "^name: ste"

# The linter ships inside the skill and runs from the installed copy.
lint=$(find ~/.claude/plugins -path "*skills/ste/scripts/ste.py" | head -1)
check "installed ste.py found" test -f "$lint"
# lint exits 1 on findings: a crash (exit 2) or a silent pass (exit 0) fails this check.
check "installed ste.py lint flags a violation" bash -c \
  "echo 'We basically set up the buffer; e.g. it.' | python3 '$lint' lint | grep '^-:1: semicolon'; \
   s=(\${PIPESTATUS[@]}); [[ \${s[1]} == 1 && \${s[2]} == 0 ]]"
check "installed ste.py lint passes clean text" bash -c "echo 'The kernel reads the tile.' | python3 '$lint' lint"
semis() { printf '%s\n' "$@" | python3 "$lint" lint | grep -o '^-:[0-9]*: semicolon' | tr '\n' ' '; }
export -f semis; export lint
check "lint skips code nested in a markdown fence, keeps the wrapper's prose" bash -c '[[ $(semis \
  "\`\`\`markdown" "The kernel reads the tile." "\`\`\`cpp" "int a; int b;" "\`\`\`" "Tail; prose." "\`\`\`") \
  == "-:6: semicolon " ]]'
check "lint keeps the prose between a markdown wrapper and a later code block" bash -c '[[ $(semis \
  "\`\`\`markdown" "prose" "\`\`\`" "Outer; prose." "\`\`\`cpp" "int a; int b;" "\`\`\`" "Final; prose.") \
  == "-:4: semicolon -:8: semicolon " ]]'
check "ste.py build downloads and parses the dictionary" python3 "$lint" build
check "dictionary flags 'utilize' with its alternative" bash -c "echo 'The kernel utilizes the tile.' | python3 '$lint' lint | grep -q 'utilizes -> USE'"

(( fail )) && echo "RESULT: FAIL" || echo "RESULT: PASS"
exit $fail
